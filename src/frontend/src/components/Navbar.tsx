export function Navbar() {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark px-4">
      <a className="navbar-brand fw-bold" href="#">
        Security Dashboard
      </a>

      <button
        className="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNav"
        aria-controls="navbarNav"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span className="navbar-toggler-icon"></span>
      </button>

      <div className="collapse navbar-collapse" id="navbarNav">
        <ul className="navbar-nav ms-auto">
          <li className="nav-item">
            <a className="nav-link text-white" href="/profile">
              <i className="bi bi-person-circle me-1"></i> Profile
            </a>
          </li>
          <li className="nav-item">
            <a className="nav-link text-white" href="/settings">
              <i className="bi bi-gear me-1"></i> Settings
            </a>
          </li>
          <li className="nav-item">
            <a className="nav-link text-danger" href="/logout">
              <i className="bi bi-box-arrow-right me-1"></i> Logout
            </a>
          </li>
        </ul>
      </div>
    </nav>
  );
}
