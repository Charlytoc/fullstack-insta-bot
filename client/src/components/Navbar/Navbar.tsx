import { Link } from "react-router-dom"
import "./navbar.css"
export const Navbar = () => {
    return (
        <nav>
            <section className="lobster-regular">
                ManageMe<strong>AI</strong>
            </section>
            <section>
                
                <Link to={"login"} >
                Login 
                </Link>
                <Link to={"signup"} >
                Signup 
                </Link>
            </section>
        </nav>
    )
}