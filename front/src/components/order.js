import React, {useCallback, useEffect, useMemo, useRef, useState} from "react";
import {get_route_with_args, get_url} from "../utils/url";
import axios from "axios";
import {Loading} from "./loading";
import {BasketRecap} from "./basket";
import {useNavigate, useLocation} from "react-router-dom";
import {FormWithContext, InputTextField, SelectField, SubmitButton} from "./form";


function OrderInformation({ordered, info = true}) {
    return <><h2>Informations à propos de cette commande</h2>
        <p>
            Cette réservation a été crée le <strong>{new Date(ordered.createdAt).toLocaleDateString('fr-fr', {
            minute: "2-digit",
            hour: "2-digit"
        })}</strong>.
        </p>
        {ordered.payment_status ? <>
            <p>
                <strong>
                    Cette commande a été payée.
                </strong>
            </p>
            <p>
                Vous pouvez retrouver un <strong>duplicata de votre facture <a 
                href={`http://127.0.0.1:8000/orders/invoice/${ordered.order_number}/${ordered.secrets}`}
                     target="_blank" rel="noreferrer">ICI</a></strong>.
            </p>
        </> : <><p>
            Notre site e-commerce prend en considération un stock disponible.<br/>
            Nous ne vendons pas un produit qui n'est pas en stock.<br/>
            Vos quantités seront réservées uniquement au moment du paiement.<br/>
            Si le paiement de la reservation est effective, la reservation sera permanent.
        </p>
            {ordered.ordered_is_enable ? <>
                <p>
                    Cette réservation est <strong>active</strong> jusqu'au <strong>
                    {new Date(ordered.effective_end_time_payment).toLocaleDateString('fr-fr', {
                        minute: "2-digit",
                        hour: "2-digit"
                    })}</strong>.
                </p>
                <p>
                    Si vous ne procédez pas au paiement de cette commande avant l'échéance,<br/>
                    la réservation sera annulée et vous pourrez constituer une autre résérvation.
                </p>
            </> : <>
                <p>
                    Cette réservation est <strong>inactive</strong>.<br/>
                    Son échéance était le {new Date(ordered.effective_end_time_payment).toLocaleDateString('fr-fr', {
                    minute: "2-digit",
                    hour: "2-digit"
                })}.
                </p>
                <p>
                    Vous ne pouvez plus procéder au paiement ni renseigner vos coordonnées.
                </p>
                <p>
                    Vous pourrez <strong>refaire une autre réservation dans au plus 25 minutes.</strong><br/>
                    Cette réservation sera bien entendue supprimer de nos bases de données.
                </p>
            </>}
        </>}
        {ordered.ordered_is_enable && info && <section>
            <h2>Mes informations...</h2>
            {ordered.phone && <p><strong>Tél:</strong> {ordered.phone}</p>}
            {ordered.email && <p><strong>Email:</strong> {ordered.email}</p>}
            {ordered.address.map((order_address, i) => <div key={i}>
                    {i === 0 ? <p><strong>Adresse de livraison</strong></p> :
                        <p><strong>Adresse de facturation</strong></p>}
                    <p><strong>{order_address.last_name} {order_address.first_name}</strong></p>
                    {order_address.address}<br/>
                    {order_address.address2 && <>
                        {order_address.address2}<br/>
                    </>}

                    {order_address.postal_code}, {order_address.city}<br/>
                    France<br/>
                </div>
            )}
        </section>}
    </>
}


export function Checkout() {
    const [data, setData] = useState(null)
    const {search} = useLocation()
    const history = useNavigate()
    const query = useMemo(() => new URLSearchParams(search), [search]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const path = get_route_with_args('sale_api:ordered-detail',
                    [localStorage.getItem('order')])
                const url = get_url(path, null)
                const res = await axios(url.href)
                setData(res.data)
            } catch (error) {
                setData({})
            }
        }

        fetchData().then(() => null)
    }, [])

    useEffect(() => {
        if (query.get("success")) {
            setTimeout(() => {
                history("/checkout")
            }, 10000)
        }
    }, [query, history])

    const checkoutSubmit = useCallback((data) => {
        const doAPost = async () => {
            const path = get_route_with_args('sale_api:ordered-payment',
                [localStorage.getItem('order')])
            const url = get_url(path, null)
            try {
                const res = await axios.post(
                    url.href, {}
                )
                if (res.data.checkout_url) {
                    window.location.assign(res.data.checkout_url)
                }
            } catch ({response}) {
            }
        }

        doAPost().then(() => null)
    }, [])

    if (data === null) {
        return <Loading/>
    }

    if (Object.keys(data).length === 0) {
        return <p>Cette commande n'existe pas.</p>
    }

    return <section className="order">
        <h2>Commande #{data.order_number}</h2>
        <section>
            <h2>Récapitulatif de cette commande</h2>
            <BasketRecap order={data} products={data.from_ordered}/>
        </section>
        <section>
            <OrderInformation ordered={data} info={false}/>
        </section>
        <section className="order_form">
            {query.get("success") ? <>
                <h2>En cours de traitement !</h2>
                <p>Le paiement est en cours de traitement, nous avons bien reçu votre requête.</p>
                <p>
                    Patientez quelques instants..(10secs) Vous allez être redirigé.
                </p>
            </> : <>
                <h2>Mes informations...</h2>
                {data.phone && <p><strong>Tél:</strong> {data.phone}</p>}
                {data.email && <p><strong>Email:</strong> {data.email}</p>}
                {data.address.map((order_address, i) => <div key={i}>
                        {i === 0 ? <p><strong>Adresse de livraison</strong></p> :
                            <p><strong>Adresse de facturation</strong></p>}
                        <p><strong>{order_address.last_name} {order_address.first_name}</strong></p>
                        {order_address.address}<br/>
                        {order_address.address2 && <>
                            {order_address.address2}<br/>
                        </>}

                        {order_address.postal_code}, {order_address.city}<br/>
                        France<br/>
                    </div>
                )}
                {!data.payment_status && <>
                <h2>Formulaire de paiement</h2>
                <FormWithContext className="form_fill_3" onSubmit={checkoutSubmit}>
                    <SubmitButton>Payer {parseFloat(data.AMOUNT_FINAL).toFixed(2)} EUR</SubmitButton>
                </FormWithContext>
                </>}
            </>}
        </section>
    </section>
}


function Order() {
    const [data, setData] = useState(null)
    const [formError, setFormError] = useState(null)
    const delivery_address = useRef()
    const history = useNavigate()
    const i = useRef(0)

    useEffect(() => {
        const fetchData = async () => {
            try {
                const path = get_route_with_args('sale_api:ordered-detail',
                    [localStorage.getItem('order')])
                const url = get_url(path, null)
                const res = await axios(url.href)
                setData(res.data)
            } catch (error) {
                setData({})
            }
        }

        fetchData().then(() => null)
    }, [])

    const orderSubmit = useCallback((data) => {
        const data_copy = {...data}
        if (i.current === 1) {

            for (const name in data) {
                if (name.match(new RegExp('^([^_]+)_1_(.+)$'))) {
                    delete data_copy[name]
                }
            }
        }

        const doAPost = async () => {
            const path = get_route_with_args('sale_api:ordered-detail',
                [localStorage.getItem('order')])
            const url = get_url(path, null)
            try {
                const res = await axios.patch(
                    url.href, data_copy
                )
                setData(res.data)
                setFormError(null)
            } catch ({response}) {
                if (response.status === 400) {
                    setFormError(response.data)
                }
            }
        }

        doAPost().then(() => null)
    }, [])

    const defaultValues = useMemo(() => {
        const dv = {}
        if (data && Object.keys(data).length > 0) {
            dv.email = data.email
            dv.phone = data.phone
            dv.delivery_mode = data.delivery_mode
            data.address.forEach((order_address, i) => {
                dv[`address_${i}_first_name`] = order_address.first_name
                dv[`address_${i}_last_name`] = order_address.last_name
                dv[`address_${i}_address`] = order_address.address
                dv[`address_${i}_address2`] = order_address.address2
                dv[`address_${i}_postal_code`] = order_address.postal_code
                dv[`address_${i}_city`] = order_address.city
            })
        }
        return dv
    }, [data])

    if (data === null) {
        return <Loading/>
    }

    if (Object.keys(data).length === 0) {
        return <p>Cette commande n'existe pas.</p>
    }

    return <section className="order">
        <h2>Commande #{data.order_number}</h2>
        <section>
            <h2>Récapitulatif de cette commande</h2>
            <BasketRecap order={data} products={data.from_ordered}/>
        </section>
        <section>
            <OrderInformation ordered={data}/>
        </section>
        {data.ordered_is_enable && <section>
            <h2>Formulaire d'informations générales</h2>
            <FormWithContext className={"order_data"} defaultValue={defaultValues} onSubmit={orderSubmit}
                             formError={formError}>
                <div className="order_form">
                    <InputTextField name={"email"}>Email :</InputTextField>
                    <InputTextField name={"phone"}>Téléphone :</InputTextField>
                </div>
                <div className="order_form">
                    <SelectField name={"delivery_mode"} labelText={"Mode de livraison"}>
                        {data.DELIVERY_MODE_CHOICES && data.DELIVERY_MODE_CHOICES.map((choice, i) =>
                            <option key={i} value={choice[0]}>{choice[1]}</option>
                        )}
                    </SelectField>
                </div>
                <div className="order_form size_2">
                    <div className="form_fill_2">
                        <section id="delivery_address" ref={delivery_address}>
                            <h3>Adresse de livraison :</h3>
                            <div>
                                <InputTextField index={0} name={`address_0_first_name`}>Prénom :</InputTextField>
                            </div>
                            <div>
                                <InputTextField index={0} name={"address_0_last_name"}>Nom :</InputTextField>
                            </div>
                            <InputTextField index={0} name={"address_0_address"}>Adresse ligne 1 :</InputTextField>
                            <InputTextField index={0} name={"address_0_address2"}>Adresse ligne 2 :</InputTextField>
                            <InputTextField index={0} name={"address_0_postal_code"}>Code postal :</InputTextField>
                            <InputTextField index={0} name={"address_0_city"}>Ville :</InputTextField>
                        </section>
                        <section id="facturation_address">
                            <h3>Adresse de facturation</h3>
                            <div>
                                <InputTextField index={1} name={"address_1_first_name"}>Prénom :</InputTextField>
                            </div>
                            <div>
                                <InputTextField index={1} name={"address_1_last_name"}>Nom :</InputTextField>
                            </div>
                            <InputTextField index={1} name={"address_1_address"}>Adresse ligne 1 :</InputTextField>
                            <InputTextField index={1} name={"address_1_address2"}>Adresse ligne 2 :</InputTextField>
                            <InputTextField index={1} name={"address_1_postal_code"}>Code postal :</InputTextField>
                            <InputTextField index={1} name={"address_1_city"}>Ville :</InputTextField>
                        </section>
                        <div role="group" className="btn-group">
                            <SubmitButton>Mettre à jour</SubmitButton>
                            <button onClick={(e) => {
                                delivery_address.current.classList.toggle("expand")
                                i.current = (i.current + 1) % 2;
                                e.currentTarget.innerText = ["Facturation identique à la livraison", "Facturation diffère de la livraison"][i.current];
                            }} type="button">Facturation identique à la livraison
                            </button>
                            {data.CAN_PAY &&
                            <button onClick={() => history("/checkout")} type="button">
                                Passer au paiement >>
                            </button>}
                        </div>
                    </div>
                </div>
            </FormWithContext>
        </section>}
    </section>
}

export default Order