import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from .osint.otx_client import OTXClient
from ..db.models import IntelEvent
from ..database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Scheduler service for running periodic OSINT collection jobs.
    
    Features:
    - Cron-like job scheduling
    - Support for multiple OSINT adapters
    - Configurable intervals
    - No-op mode for CI environments
    - Error handling and logging
    """
    
    def __init__(self):
        """Initialize the scheduler service"""
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            executors={'default': AsyncIOExecutor()},
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 30
            }
        )
        self.otx_client = OTXClient()
        self.is_ci = os.getenv('CI', '').lower() in ('true', '1', 'yes')
        
        # Default indicators to monitor (can be configured via environment)
        self.default_indicators = self._load_default_indicators()
        
    def _load_default_indicators(self) -> List[Dict[str, str]]:
        """Load default indicators to monitor from environment or use defaults"""
        indicators_env = os.getenv('OTX_MONITOR_INDICATORS')
        if indicators_env:
            try:
                # Expected format: "ip:1.2.3.4,domain:example.com,hash:abc123"
                indicators = []
                for item in indicators_env.split(','):
                    if ':' in item:
                        indicator_type, value = item.split(':', 1)
                        indicators.append({
                            'type': indicator_type.strip(),
                            'value': value.strip()
                        })
                return indicators
            except Exception as e:
                logger.warning(f"Failed to parse OTX_MONITOR_INDICATORS: {e}")
        
        # Default test indicators
        return [
            {'type': 'ip', 'value': '8.8.8.8'},
            {'type': 'domain', 'value': 'google.com'},
            {'type': 'hash', 'value': 'd41d8cd98f00b204e9800998ecf8427e'}  # Empty file MD5
        ]
    
    async def start(self):
        """Start the scheduler"""
        if self.is_ci:
            logger.info("Running in CI mode - scheduler will be no-op")
            return
        
        logger.info("Starting scheduler service")
        
        # Add OTX collection job
        interval_minutes = int(os.getenv('OTX_COLLECTION_INTERVAL_MINUTES', '60'))
        self.scheduler.add_job(
            self.collect_otx_intelligence,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='otx_collection',
            name='OTX Intelligence Collection',
            replace_existing=True
        )
        
        # Add daily cleanup job
        self.scheduler.add_job(
            self.cleanup_old_events,
            trigger=CronTrigger(hour=2, minute=0),  # Run at 2 AM daily
            id='cleanup_old_events',
            name='Cleanup Old Intel Events',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler started with OTX collection every {interval_minutes} minutes")
    
    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    async def collect_otx_intelligence(self):
        """
        Collect intelligence from OTX for configured indicators.
        This is the main job that runs on schedule.
        """
        logger.info("Starting OTX intelligence collection")
        
        try:
            # Check OTX client health
            health = self.otx_client.health_check()
            if health['status'] != 'healthy':
                logger.error(f"OTX client unhealthy: {health['message']}")
                return
            
            collected_count = 0
            for indicator in self.default_indicators:
                try:
                    intel_event = await self._collect_indicator_intelligence(
                        indicator['type'], 
                        indicator['value']
                    )
                    
                    if intel_event:
                        await self._store_intel_event(intel_event)
                        collected_count += 1
                        logger.info(f"Collected intelligence for {indicator['type']}: {indicator['value']}")
                    
                except Exception as e:
                    logger.error(f"Failed to collect intelligence for {indicator}: {e}")
                    continue
            
            logger.info(f"OTX intelligence collection completed. Collected {collected_count} events")
            
        except Exception as e:
            logger.error(f"OTX intelligence collection failed: {e}")
    
    async def _collect_indicator_intelligence(self, indicator_type: str, value: str) -> Optional[IntelEvent]:
        """
        Collect intelligence for a specific indicator.
        
        Args:
            indicator_type: Type of indicator (ip, domain, hash)
            value: Indicator value
            
        Returns:
            IntelEvent if successful, None otherwise
        """
        try:
            if indicator_type == 'ip':
                return self.otx_client.get_ip_reputation(value)
            elif indicator_type == 'domain':
                return self.otx_client.get_domain_reputation(value)
            elif indicator_type == 'hash':
                return self.otx_client.get_file_hash_reputation(value)
            else:
                logger.warning(f"Unknown indicator type: {indicator_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to collect intelligence for {indicator_type}:{value}: {e}")
            return None
    
    async def _store_intel_event(self, intel_event: IntelEvent):
        """
        Store intelligence event in database.
        
        Args:
            intel_event: IntelEvent to store
        """
        try:
            # Convert Pydantic model to dict for MongoDB
            event_dict = intel_event.dict(by_alias=True)
            event_dict['_id'] = event_dict.pop('id')  # MongoDB uses _id
            
            # Insert into intel_events collection
            result = await db.intel_events.insert_one(event_dict)
            logger.debug(f"Stored intel event with ID: {result.inserted_id}")
            
        except Exception as e:
            logger.error(f"Failed to store intel event: {e}")
            raise
    
    async def cleanup_old_events(self):
        """
        Clean up old intelligence events to prevent database bloat.
        Removes events older than configured retention period.
        """
        try:
            retention_days = int(os.getenv('INTEL_EVENTS_RETENTION_DAYS', '30'))
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            result = await db.intel_events.delete_many({
                'created_at': {'$lt': cutoff_date}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} old intel events (older than {retention_days} days)")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old events: {e}")
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get current scheduler status and job information.
        
        Returns:
            Dictionary with scheduler status
        """
        if self.is_ci:
            return {
                'status': 'ci_mode',
                'message': 'Scheduler running in CI mode (no-op)',
                'jobs': []
            }
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'status': 'running' if self.scheduler.running else 'stopped',
            'message': f'Scheduler is {"running" if self.scheduler.running else "stopped"}',
            'jobs': jobs,
            'otx_client_health': self.otx_client.health_check()
        }
    
    async def trigger_manual_collection(self) -> Dict[str, Any]:
        """
        Manually trigger intelligence collection (for testing/debugging).
        
        Returns:
            Dictionary with collection results
        """
        logger.info("Manual OTX intelligence collection triggered")
        
        try:
            await self.collect_otx_intelligence()
            return {
                'status': 'success',
                'message': 'Manual collection completed successfully'
            }
        except Exception as e:
            logger.error(f"Manual collection failed: {e}")
            return {
                'status': 'error',
                'message': f'Manual collection failed: {str(e)}'
            }


# Global scheduler instance
scheduler_service = SchedulerService()

