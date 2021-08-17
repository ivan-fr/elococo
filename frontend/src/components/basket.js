import React, {useCallback, useEffect, useMemo, useState} from "react";
import {Link} from "react-router-dom";
import {CheckBoxField, FormWithContext, InputTextField, SelectField, SubmitButton} from "./form";
import {get_route_with_args, get_url} from "../utils/url";
import axios from "axios";
import {Loading} from "./loading";


export function BasketRecap({order, products}) {
    console.log(order.delivery_value)
    return <div className="table-responsive">
        <table className="table table-striped">
            <thead>
            <tr>
                <th scope="col">#</th>
                <th scope="col">Nom du produit</th>
                <th scope="col">Prix unitaire (HT)</th>
                <th scope="col">Dont réduction (%)</th>
                <th scope="col">Quantité</th>
                <th scope="col">Sous Total</th>
            </tr>
            </thead>
            <tbody>
            {products && products.map((product, i) =>
                <tr key={i}>
                    <th scope="row">{i + 1}</th>
                    <td>
                        <Link to={`/catalogue/${product.slug}`}>{product.name}</Link>
                    </td>
                    <td>{product.price_exact_ht}€</td>
                    <td>{product.effective_reduction > 0 ?
                        <>-{product.effective_reduction}%</>
                        : <>Pas de reduction.</>}
                    </td>
                    <td>{product.quantity}</td>
                    <td>{parseFloat(product.price_exact_ht_with_quantity).toFixed(2)}€</td>
                </tr>)}

            {order.price_exact_ht_with_quantity_sum &&
            <tr>
                <td><strong>Total (HT)</strong></td>
                <td colSpan="4"/>
                <td>{parseFloat(order.price_exact_ht_with_quantity_sum).toFixed(2)}€</td>
            </tr>}

            {order.promo && order.promo.value ? <>
                    <tr>
                        <td><strong>Promo</strong></td>
                        <td colSpan="4"/>
                        {order.promo.type === "pe" ?
                            <td>-{order.promo.value}%</td>
                            :
                            <td>-{order.promo.value}€</td>
                        }
                    </tr>
                    <tr>
                        <td><strong>Nouveau Total (HT)</strong></td>
                        <td colSpan="4"/>
                        <td>{parseFloat(order.price_exact_ht_with_quantity_promo_sum).toFixed(2)}€</td>
                    </tr>
                    <tr>
                        <td><strong>TVA 20.00%</strong></td>
                        <td colSpan="4"/>
                        <td>{parseFloat(order.deduce_tva_promo).toFixed(2)}€</td>
                    </tr>
                    <tr>
                        <td><strong>Total (TTC)</strong></td>
                        <td colSpan="4"/>
                        <td>
                            <strong>{parseFloat(order.price_exact_ttc_with_quantity_promo_sum).toFixed(2)}€</strong>
                        </td>
                    </tr>
                </>
                : <>
                    <tr>
                        <td><strong>TVA 20.00%</strong></td>
                        <td colSpan="4"/>
                        <td>{parseFloat(order.deduce_tva).toFixed(2)}€</td>
                    </tr>
                    <tr>
                        <td><strong>TOTAL (TTC)</strong></td>
                        <td colSpan="4"/>
                        <td><strong>{parseFloat(order.price_exact_ttc_with_quantity_sum).toFixed(2)}€</strong></td>
                    </tr>
                </>}

            {65. <= parseFloat(order.price_exact_ttc_with_quantity_sum) ? <>
                    <tr>
                        <td><strong>Livraison</strong></td>
                        <td colSpan="4"/>
                        <td><strong>GRATUIT</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Total (livraison)</strong></td>
                        <td colSpan="4"/>
                        <td><strong>{parseFloat(order.AMOUNT_FINAL).toFixed(2)}€</strong></td>
                    </tr>
                </>
                : <>
                    <tr>
                        <td><strong>Livraison</strong></td>
                        <td colSpan="4"/>
                        {order.delivery_value === null ?
                            <td><strong>à définir</strong></td>
                            :
                            <td><strong>{order.delivery_value}€</strong></td>
                        }
                    </tr>
                    <tr>
                        <td><strong>Total (livraison)</strong></td>
                        <td colSpan="4"/>
                        {order.delivery_value === null ?
                        <td><strong>à définir</strong></td>
                        :
                        <td><strong>{parseFloat(order.AMOUNT_FINAL).toFixed(2)}€</strong></td>
                        }
                    </tr>
                </>}
            </tbody>
        </table>
    </div>

}


function Basket() {
    const [data, setData] = useState(null)
    const [formUpdateBasketError, setFormUpdateBasketError] = useState(null)
    const [formPromoBasketError, setFormPromoBasketError] = useState(null)
    const [msg, setMsg] = useState("")
    const [doEffect, setDoEffect] = useState(false)

    useEffect(() => {
        const doAFetch = async () => {
            const path = get_route_with_args('catalogue_api:product-basket-surface',
                [localStorage.getItem('basket'), localStorage.getItem('promo')]
            )
            const url = get_url(path, null)
            try {
                const res = await axios(url.href)
                setData(res.data)
                localStorage.setItem('basket', res.data.basket)
                localStorage.setItem('basket_len', res.data.basket_len)
                if (!res.data.promo) {
                    localStorage.removeItem('promo')
                }
            } catch ({response}) {
                localStorage.removeItem('promo')
                setData({})
            }
        }

        doAFetch().then(() => null)
    }, [doEffect])

    const updateBasketSubmit = useCallback((data) => {
        const patchData = async () => {
            try {
                const path = get_route_with_args('catalogue_api:product-basket-update', [])
                const url = get_url(path, null)
                const response = await axios.post(url.href, {...data, 'basket': localStorage.getItem('basket')})
                localStorage.setItem('basket_len', response.data.basket_len)
                localStorage.setItem('basket', response.data.basket)
                setFormUpdateBasketError(null)
                setDoEffect(d => !d)

                if (response.status === 205) {
                    setMsg("Des mise à jour sur le panier ont dû être éffectué pour correspondre au catalogue.")
                }
            } catch ({response}) {
                if (response.status === 400) {
                    setFormUpdateBasketError(response.data)
                }
            }
        }

        patchData().then(() => null)
    }, [])

    const promoBasketSubmit = useCallback((data) => {
        const doAPost = async () => {
            const path = get_route_with_args('catalogue_api:product-basket-promo', [])
            const url = get_url(path, null)
            try {
                const res = await axios.post(
                    url.href, {
                        'basket': localStorage.getItem('basket'),
                        'promo': data.promo
                    }
                )
                localStorage.setItem('basket', res.data.basket)
                if (res.data.promo && res.data.promo.code) {
                    localStorage.setItem('promo', res.data.promo.code)
                }
                setFormPromoBasketError(null)
            } catch ({response}) {
                localStorage.removeItem('promo')
                if (response.status === 404) {
                    setFormPromoBasketError(
                        {'promo': ["Ce code n'existe pas ou n'est pas compatible avec votre panier."]}
                    )
                }
            }
            setDoEffect(d => !d)
        }

        doAPost().then(() => null)
    }, [])

    const bookSubmit = useCallback((data) => {
        const doAPost = async () => {
            const path = get_route_with_args('sale_api:product-list', [])
            const url = get_url(path, null)
            try {
                const res = await axios.post(
                    url.href, {
                        'basket': localStorage.getItem('basket'),
                        'promo': data.promo
                    }
                )
                localStorage.setItem('order', res.data.order)
            } catch ({response}) {
                if (response.status === 401) {
                    localStorage.setItem('basket_len', response.data.basket_len)
                    localStorage.setItem('basket', response.data.basket)
                    if (response.data.promo && response.data.promo.code) {
                        localStorage.setItem('promo', response.data.promo.code)
                    } else {
                        localStorage.removeItem('promo')
                    }
                    setMsg("Des mise à jour sur le panier ont dû être éffectué pour correspondre au catalogue.")
                } else {
                    alert('Panier invalide, veuillez recharger la page.')
                }
                setDoEffect(d => !d)
            }
        }

        doAPost().then(() => null)
    }, [])

    const defaultValues = useMemo(() => {
        const df = {}
        if (data && data.products) {
            data.products.forEach((product) => {
                df[`product_${product.slug}_quantity`] = product.effective_basket_quantity
                df[`product_${product.slug}_remove`] = false
            })
        }
        return df
    }, [data])

    if (data === null) {
        return <Loading/>
    }

    if (Object.keys(data).length === 0) {
        return <p>Votre panier est vide.</p>
    }

    return <>
        {msg && msg !== "" && <p>{msg}</p>}
        <FormWithContext id="basket_form" defaultValue={defaultValues} onSubmit={updateBasketSubmit}
                         formError={formUpdateBasketError} many={true}>
            <div className="table-responsive">
                <table className="table table-striped">
                    <thead>
                    <tr>
                        <th scope="col">#</th>
                        <th scope="col">Nom du produit</th>
                        <th scope="col">Prix unitaire (HT)</th>
                        <th scope="col">Dont réduction (%)</th>
                        <th scope="col">Quantité</th>
                        <th scope="col">Sous Total</th>
                        <th scope="col">Supprimer ?</th>
                    </tr>
                    </thead>
                    <tbody>
                    {data.products && data.products.map((product, i) =>
                        <tr key={i}>
                            <th scope="row">{i + 1}</th>
                            <td>
                                <Link to={`/catalogue/${product.slug}`}>{product.name}</Link>
                            </td>
                            <td>{product.price_exact_ht}€</td>
                            <td>{product.effective_reduction > 0 ?
                                <>-{product.effective_reduction}%</>
                                : <>Pas de reduction.</>}
                            </td>
                            <td>
                                <SelectField index={i} name={`product_${product.slug}_quantity`} labelText={null}>
                                    {
                                        [...Array(Math.min(3, product.stock)).keys()].map(i =>
                                            <option key={i} value={i + 1}>{i + 1}</option>
                                        )
                                    }
                                </SelectField>
                            </td>
                            <td>{product.price_exact_ht_with_quantity}€</td>
                            <td><CheckBoxField index={i} name={`product_${product.slug}_remove`}/></td>
                        </tr>)}

                    {data.price_exact_ht_with_quantity__sum &&
                    <tr>
                        <td><strong>Total (HT)</strong></td>
                        <td colSpan="4"/>
                        <td>{data.price_exact_ht_with_quantity__sum}€</td>
                        <td/>
                    </tr>}

                    {data.promo && data.promo.value ? <>
                            <tr>
                                <td><strong>Promo</strong></td>
                                <td colSpan="4"/>
                                {data.promo.type === "pe" ?
                                    <td>-{data.promo.value}%</td>
                                    :
                                    <td>-{data.promo.value}€</td>
                                }
                                <td/>
                            </tr>
                            <tr>
                                <td><strong>Nouveau Total (HT)</strong></td>
                                <td colSpan="4"/>
                                <td>{data.price_exact_ht_with_quantity_promo__sum}€</td>
                                <td/>
                            </tr>
                            <tr>
                                <td><strong>TVA 20.00%</strong></td>
                                <td colSpan="4"/>
                                <td>{data.deduce_tva_promo}€</td>
                                <td/>
                            </tr>
                            <tr>
                                <td><strong>Total (TTC)</strong></td>
                                <td colSpan="4"/>
                                <td>
                                    <strong>{data.price_exact_ttc_with_quantity_promo__sum}€</strong>
                                </td>
                                <td/>
                            </tr>
                        </>
                        : <>
                            <tr>
                                <td><strong>TVA 20.00%</strong></td>
                                <td colSpan="4"/>
                                <td>{data.deduce_tva}€</td>
                                <td/>
                            </tr>
                            <tr>
                                <td><strong>TOTAL (TTC)</strong></td>
                                <td colSpan="4"/>
                                <td><strong>{data.price_exact_ttc_with_quantity__sum}€</strong></td>
                                <td/>
                            </tr>
                        </>}
                    </tbody>
                </table>
            </div>
            <SubmitButton ifChange={true}>Valider les changements</SubmitButton>
            {65 <= data.price_exact_ttc_with_quantity__sum ?
                <p><strong>La livraison est offerte.</strong></p>
                :
                <p><strong>Un tarif de livraison sera à prendre en compte.</strong></p>}
        </FormWithContext>
        <div id='promo_form'>
            <FormWithContext defaultValue={{}} onSubmit={promoBasketSubmit} formError={formPromoBasketError}>
                <div>
                    <InputTextField name="promo">Code promo :</InputTextField>
                </div>
                <div>
                    <SubmitButton>Envoyer</SubmitButton>
                </div>
            </FormWithContext>
        </div>
        <div id='book_form'>
            <FormWithContext defaultValue={{}} onSubmit={bookSubmit}>
                <SubmitButton>Commander</SubmitButton>
            </FormWithContext>
        </div>
    </>
}

export default Basket