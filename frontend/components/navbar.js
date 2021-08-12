import React from 'react'
import Link from 'next/link'


function NavBar() {
    return <nav className="navbar">
        <ul>
            <li className="is-active">
                <Link href="/"><a>Boutique</a></Link>
            </li>
        </ul>
        <ul>
            <li>
                <Link href="/"><a>Retrouver une commande</a></Link>
            </li>
            <li>
                <Link href="/"><a>Completer ma commande (1/3)</a></Link>
            </li>
            <li id="navbar-basket">
                <Link href="/"><a>Panier <span>0</span></a></Link>
            </li>
        </ul>
    </nav>
}

export default NavBar;
