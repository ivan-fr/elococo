import React, {useCallback, useEffect, useRef, useState} from 'react'
import {Link, useLocation} from 'react-router-dom'
import {get_route_with_args, get_url} from "../utils/url";
import axios from "axios";

function NavBar() {
    const [showBasket, setShowBasket] = useState(false)
    const [, setRefresh] = useState(false)
    const basketSign = useRef(localStorage.getItem('basket'))
    const promo = useRef(localStorage.getItem('promo'))
    const {pathname, search} = useLocation()
    const data = useRef(null)

    const basket_callback = useCallback((e) => {
        const doAFetch = async () => {
            const path = get_route_with_args('catalogue_api:product-basket-surface',
                [localStorage.getItem('basket'), localStorage.getItem('promo')]
            )
            const url = get_url(path, null)
            try {
                const res = await axios(url.href)
                data.current = res.data
                localStorage.setItem('basket', res.data.basket)
                localStorage.setItem('basket_len', res.data.basket_len)
            } catch ({response}) {
                data.current = {}
            }
            setShowBasket(s => {
                if (s) {
                    setRefresh(r => !r)
                    return s
                }
                return true
            })
        }

        if (pathname !== "/basket"
            && ((!data.current && e) || localStorage.getItem('basket') !== basketSign.current
                || localStorage.getItem('promo') !== promo.current)) {
            basketSign.current = localStorage.getItem('basket')
            doAFetch().then(() => null)
        } else if (data.current) {
            setShowBasket(true)
        }
    }, [pathname])

    const leave_callback = useCallback(() => {
        setShowBasket(false)
    }, [])

    useEffect(() => {
        const urlSearchParams = new URLSearchParams(search)
        if (urlSearchParams.get("show_surface_basket")) {
            basket_callback(null)
        }
    }, [search, basket_callback])

    return <nav className="navbar">
        <ul>
            <li className="is-active">
                <Link to="/">Boutique</Link>
            </li>
        </ul>
        <ul onMouseLeave={leave_callback}>
            {localStorage.getItem('order') && <li>
                <Link to="/order">Ma commande</Link>
            </li>}
            {pathname !== "/basket" && <li id="navbar-basket">
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
                                <Link onClick={() => setShowBasket(false)} to="/basket">Voir mon panier</Link>
                            </li>
                        </ul>
                    </> : <ul>
                        <li>
                            Votre panier est vide.
                        </li>
                    </ul>}
                </nav>}
            </li>}
        </ul>
    </nav>
}

export default NavBar;
