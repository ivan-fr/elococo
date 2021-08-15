import React, {useEffect, useState} from "react";
import {get_route_with_args, get_url} from "../utils/url";
import axios from "axios";
import {Loading} from "./loading";
import {Link} from "react-router-dom";
import {CheckBoxField, FormField, FormWithContext, SelectField, SubmitButton} from "./form";

function Basket() {
    const [data, setData] = useState(null)

    useEffect(() => {
        const doAFetch = async () => {
            const path = get_route_with_args('catalogue_api:product-basket-surface',
                [localStorage.getItem('basket'), localStorage.getItem('promo')]
            )
            const url = get_url(path, null)
            try {
                const res = await axios(url.href)
                setData(res.data)
                localStorage.setItem('basket', res.data.basket_sign)
            } catch ({response}) {
                setData({})
            }
        }

        doAFetch().then(() => null)
    }, [])

    if (data === null) {
        return <Loading/>
    }

    const defaultValue = {}

    if (data.products) {
        data.products.forEach((product, i) => {
            defaultValue[`product-${i}-quantity`] = product.effective_basket_quantity
            defaultValue[`product-${i}-remove`] = false
        })
    }

    return <><FormWithContext id="basket_form" defaultValue={defaultValue}>
        <div className="table-responsive">
            <table className="table table-striped">
                <thead>
                <tr>
                    <th scope="col">#</th>
                    <th scope="col">Nom du produit</th>
                    <th scope="col">Prix unitaire (HT)</th>
                    <th scope="col">Dont réduction (%)</th>
                    <th scope="col">Quantité</th>
                    <th scope="col">Sous Total (HT)</th>
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
                            <SelectField name={`product-${i}-quantity`} labelText={null}>
                                {
                                    [...Array(Math.min(3, product.stock)).keys()].map(i =>
                                        <option key={i} value={i + 1}>{i + 1}</option>
                                    )
                                }
                            </SelectField>
                        </td>
                        <td>{product.price_exact_ht_with_quantity}€</td>
                        <td><CheckBoxField name={`product-${i}-remove`}/></td>
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
            <p><strong>Un tarif de livraison sera à prendre en compte.</strong></p>
        }
    </FormWithContext>
        <div id='promo_form'>
            <FormWithContext defaultValue={{}}>
                <div>
                    <FormField name="code_promo">Code promo :</FormField>
                </div>
                <div>
                    <SubmitButton>Envoyer</SubmitButton>
                </div>
            </FormWithContext>
        </div>
    </>
}

export default Basket