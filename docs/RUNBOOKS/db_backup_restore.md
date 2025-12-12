## Backup Procedure
```bash
mongodump --uri="$MONGO_URI" --out /backups/smbsec-$(date +%F)