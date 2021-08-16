import React, {useEffect, useState} from "react";
import {get_route_with_args, get_url} from "../utils/url";
import axios from "axios";
import {Loading} from "./loading";
import {BasketRecap} from "./basket";
import {Link} from "react-router-dom";
import {FormWithContext, InputTextField, SelectField, SubmitButton} from "./form";


function OrderInformation({ordered}) {
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
                Vous pouvez retrouver un <strong>duplicata de votre facture <Link
                to="/">ICI</Link></strong>.
            </p>
        </> : <><p>
            Notre site e-commerce prend en considération un stock disponible.<br/>
            Nous ne vendons pas un produit qui n'est pas en stock.<br/>
            Vos quantités seront réservées uniquement au moment du paiement.<br/>
            Si le paiement de la reservation est effective, la reservation sera permanent.
        </p>
            {ordered.ordered_is_enable ? <>
                <p>
                    Cette réservation est <strong>active</strong>
                    jusqu'au <strong>{new Date(ordered.effective_end_time_payment).toLocaleDateString('fr-fr', {
                    minute: "2-digit",
                    hour: "2-digit"
                })}</strong>.
                </p>
                <p>
                    Si vous ne procédez pas au paiement de cette commande avant l'échéance,<br/>
                    la réservation sera annulée et vous pourrez constituer une autre résérvation.
                </p>
                <p>
                    <strong>Tous nos produits sont envoyés avec un suivi.</strong><br/>
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
        <section>
            {ordered.order_address.map((order_address, i) => <div key={i}>
                    {i === 0 ? <strong>Adresse de livraison</strong> :
                        <strong>Adresse de facturation</strong>}
                    <p><strong>{order_address.last_name} {order_address.first_name}</strong></p>
                    {order_address.address}<br/>
                    {order_address.address2 && <>
                        {order_address.address2}<br/>
                    </>}

                    {order_address.postal_code}, {order_address.city}<br/>
                    France<br/>
                </div>
            )}
            <p>Tél: {ordered.phone}</p>
            <p>Email: {ordered.email}</p>
        </section>
    </>
}


function Order() {
    const [data, setData] = useState(null)

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
        <section>
            <h2>Formulaire d'informations générales</h2>
            <FormWithContext className={"order_data"}>
                <div className="order_form">
                    <InputTextField>Email :</InputTextField>
                    <InputTextField>Téléphone :</InputTextField>
                </div>
                <div className="order_form">
                    <SelectField labelText={"Mode de livraison"}>
                        {data.DELIVERY_MODE_CHOICES && data.DELIVERY_MODE_CHOICES.map((choice, i) =>
                            <option key={i} value={choice[0]}>{choice[1]}</option>
                        )}
                    </SelectField>
                </div>
                <div className="order_form size_2">
                    <div className="form_fill_2">
                        <section id="delivery_address" className={"expand"}>
                            <h3>Adresse de livraison :</h3>
                            <div>
                                <InputTextField name={"first_name"}>Prénom :</InputTextField>
                            </div>
                            <div>
                                <InputTextField name={"last_name"}>Nom :</InputTextField>
                            </div>
                            <InputTextField name={"address"}>Adresse ligne 1 :</InputTextField>
                            <InputTextField name={"address2"}>Adresse ligne 2 :</InputTextField>
                            <InputTextField name={"postal_code"}>Code postal :</InputTextField>
                            <InputTextField name={"city"}>Ville :</InputTextField>
                        </section>
                        <section id="facturation_address">
                            <h3>Adresse de facturation</h3>
                            <div>
                                <InputTextField name={"first_name"}>Prénom :</InputTextField>
                            </div>
                            <div>
                                <InputTextField name={"last_name"}>Nom :</InputTextField>
                            </div>
                            <InputTextField name={"address"}>Adresse ligne 1 :</InputTextField>
                            <InputTextField name={"address2"}>Adresse ligne 2 :</InputTextField>
                            <InputTextField name={"postal_code"}>Code postal :</InputTextField>
                            <InputTextField name={"city"}>Ville :</InputTextField>
                        </section>
                        <div role="group" className="btn-group">
                            <SubmitButton>Mettre à jour</SubmitButton>
                        </div>
                    </div>
                </div>
            </FormWithContext>
        </section>

    </section>
}

export default Order