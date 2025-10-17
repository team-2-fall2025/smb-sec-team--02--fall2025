import { NavLink } from "react-router-dom";

export function Sidebar() {
  return (
    <div
      className="bg-dark border-end p-3"
      style={{ width: "250px", minHeight: "calc(100vh - 56px)" }}
    >
      {/* <h5 className="mb-3">Navigation</h5> */}
      <ul className="nav flex-column">
        <li className="nav-item mb-2">
          <NavLink
            to="/"
            className={({ isActive }) =>
                `nav-link px-3 py-2 border-start ${
                isActive
                    ? "border-3 border-primary text-dark bg-light fw-semibold"
                    : "border-0 text-white hover:text-light"
                }`
            }
          >
            <i className="bi bi-speedometer2 me-2"></i> Dashboard
          </NavLink>
        </li>
        <li className="nav-item mb-2">
          <NavLink
            to="/assets"
            className={({ isActive }) =>
              `nav-link px-3 py-2 border-start ${
                isActive
                    ? "border-3 border-primary text-dark bg-light fw-semibold"
                    : "border-0 text-white hover:text-light"
                }`
            }
          >
            <i className="bi bi-hdd-stack me-2"></i> Assets
          </NavLink>
        </li>
        <li className="nav-item mb-2">
          <NavLink
            to="/intel"
            className={({ isActive }) =>
              `nav-link px-3 py-2 border-start ${
                isActive
                    ? "border-3 border-primary text-dark bg-light fw-semibold"
                    : "border-0 text-white hover:text-light"
                }`
            }
          >
            <i className="bi bi-lightbulb me-2"></i> Intel Events
          </NavLink>
        </li>
        <li className="nav-item mb-2">
          <NavLink
            to="/risk"
            className={({ isActive }) =>
              `nav-link px-3 py-2 border-start ${
                isActive
                    ? "border-3 border-primary text-dark bg-light fw-semibold"
                    : "border-0 text-white hover:text-light"
                }`
            }
          >
            <i className="bi bi-exclamation-triangle me-2"></i> Risk Items
          </NavLink>
        </li>
      </ul>
    </div>
  );
}
