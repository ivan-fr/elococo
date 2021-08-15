import React, {useCallback, useEffect, useRef, useState} from 'react'
import {Link} from 'react-router-dom'
import {get_route_with_args, get_url} from "../utils/url";
import axios from "axios";

function NavBar() {
    const [showBasket, setShowBasket] = useState(false)
    const basket_sign = useRef(null)
    const data = useRef(null)

    const basket_callback = useCallback(() => {
        const doAFetch = async () => {
            const path = get_route_with_args('catalogue_api:product-basket-surface',
                [current_basket, localStorage.getItem('promo')]
            )
            const url = get_url(path, null)
            try {
                const res = await axios(url.href)
                data.current = res.data
                setShowBasket(true)
                console.log(data.current)
            } catch ({response}) {

            }
        }

        const current_basket = localStorage.getItem('basket')
        let doAxios = false
        if (current_basket !== basket_sign.current) {
            basket_sign.current = current_basket
            doAxios = true
        } else if (data.current) {
            setShowBasket(true)
        }

        if (doAxios) {
            doAFetch().then(() => null)
        }
    }, [])

    const leave_callback = useCallback(() => {
        setShowBasket(false)
    }, [])

    useEffect(() => {
        window.addEventListener('storage', basket_callback)
        return () => window.removeEventListener('storage', basket_callback)
    })

    return <nav className="navbar">
        <ul>
            <li className="is-active">
                <Link to="/">Boutique</Link>
            </li>
        </ul>
        <ul onMouseLeave={leave_callback}>
            <li>
                <Link to="/">Retrouver une commande</Link>
            </li>
            <li>
                <Link to="/">Completer ma commande (1/3)</Link>
            </li>
            <li id="navbar-basket">
                <a href={"/"} onClick={(e) => e.preventDefault()}
                   onMouseEnter={basket_callback}>Panier
                    <span>{localStorage.getItem('basket_len') ? localStorage.getItem('basket_len') : 0}</span>
                </a>
                {data.current && showBasket && <nav className="active">
                    {data.current.products ? <>
                        <ul>
                            {data.current.products && data.current.products.map((product, i) =>
                                <li key={i}>
                                    <Link to={`/catalogue/${product.slug}`}>{product.name}</Link>
                                    <ul>
                                        <li>{product.effective_basket_quantity}X
                                            - {product.price_exact_ttc_with_quantity}€ (TTC)
                                        </li>
                                    </ul>
                                </li>)}
                        </ul>
                        <ul>
                            {data.current.promo ? <>
                                    <li>
                                        <strong>Promo</strong>
                                        <ul>
                                            {data.current.promo.type === "pe" ?
                                                <li>-{data.current.promo.value}%</li>
                                                :
                                                <li>-{data.current.promo.value}€</li>
                                            }
                                        </ul>
                                    </li>
                                    <li>Total
                                        (TTC) <strong>{data.current.price_exact_ttc_with_quantity_promo__sum}€</strong>
                                    </li>
                                </>
                                :
                                <li>Total (TTC) <strong>{data.current.price_exact_ttc_with_quantity__sum}€</strong></li>
                            }
                            {65 <= data.current.price_exact_ttc_with_quantity__sum ?
                                <li><strong>La livraison est offerte.</strong></li>
                                :
                                <li><strong>Un tarif de livraison sera à prendre en compte.</strong></li>
                            }
                        </ul>
                        <ul>
                            <li>
                                <Link to="/">Voir mon panier</Link>
                            </li>
                        </ul>
                    </> : <ul>
                        <li>
                            Votre panier est vide.
                        </li>
                    </ul>}
                </nav>}
            </li>
        </ul>
    </nav>
}

export default NavBar;
