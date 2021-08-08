import React from 'react'
import { Link } from 'react-router-dom'

class NavBar extends React.Component {
    render() {
        return <nav className="navbar">
            <ul>
                <li className="is-active">
                    <Link to="/">Boutique</Link>
                </li>
            </ul>
            <ul>
                <li>
                    <Link to="/">Retrouver une commande</Link>
                </li>
                <li>
                    <Link to="/">Completer ma commande (1/3)</Link>
                </li>
                <li id="navbar-basket">
                    <Link to="/">Panier <span>0</span></Link>
                </li>
            </ul>
        </nav>
    }
}

export default NavBar;
