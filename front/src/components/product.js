import React, {useCallback, useEffect, useRef, useState} from 'react';
import {Loading} from "./loading";
import axios from "axios";
import {get_route_with_args, get_url} from "../utils/url";
import {useNavigate, useParams} from "react-router-dom";
import rule from "../public/rule2.bmp"
import {FormWithContext, SelectField, SubmitButton} from "./form";

function Product() {
    const [response, setResponse] = useState(null)
    const [isError, setIsError] = useState(false)
    const [formError, setFormError] = useState(null)
    const history = useNavigate()
    let {slug} = useParams();
    const zoom_span = useRef(null)

    const zoom = useCallback((e) => {
        e.preventDefault()
        const image = e.currentTarget.cloneNode(true)
        zoom_span.current.innerHTML = ""
        zoom_span.current.appendChild(image)
    }, [zoom_span])

    useEffect(() => {
        const fetchData = async () => {
            try {
                const path = get_route_with_args('catalogue_api:product-detail', [slug])
                const url = get_url(path)
                const res = await axios(url.href)
                setResponse(res.data)
                setIsError(false)
            } catch (error) {
                setIsError(true)
            }
        }

        fetchData().then(() => null)
    }, [slug])

    const handleSubmit = useCallback((data) => {
        const patchData = async () => {
            try {
                const path = get_route_with_args('catalogue_api:product-detail', [slug])
                const url = get_url(path, null)
                const response = await axios.patch(url.href, {...data, 'basket': localStorage.getItem('basket')})
                localStorage.setItem('basket_len', response.data.basket_len)
                localStorage.setItem('basket', response.data.basket)
                setFormError(null)
                history({search: `?show_surface_basket=${response.data.basket_len}`})
            } catch ({response}) {
                if (response.status === 400) {
                    setFormError(response.data)
                }
            }
        }

        patchData().then(() => null)
    }, [slug, history])

    if (isError) {
        return <div className="catalog">Erreur lors du chargement.</div>
    }

    if (response === null) {
        return <Loading/>
    }

    return <>
        <h2>{response.name}</h2>
        <article id="detail">
            <h3>Details</h3>

            <section>
                <h2>Zoom</h2>
                <span className="image_zoom" role="status" ref={zoom_span}>
                    {response?.productimage_set && response.productimage_set &&
                    <figure className="hover_figure" onClick={zoom}>
                        <img src={response.productimage_set[0].image}
                             alt={`product ${response.name}`}/>
                        <figcaption>
                            Image du produit n°0
                        </figcaption>
                    </figure>}
            </span>
            </section>

            <div className="images">
                {response?.productimage_set && response.productimage_set.map((image, i) =>
                    <figure key={i} className="hover_figure" onClick={zoom}>
                        <img src={image.image}
                             alt={`product ${i} ${response.name}`}/>
                        <figcaption>
                            Image du produit n°{i}
                        </figcaption>
                    </figure>)}
            </div>

            {response?.enable_sale &&
            <section className="sale_infos">
                <h3>Informations de vente</h3>
                <div>
                    <p>Son prix à l'unité est de <strong>{response?.price_exact_ttc}€ TTC.</strong>
                    </p>
                    {response.effective_reduction > 0 && <>
                        <p>Il y a une réduction de <strong>-{response.effective_reduction}%</strong> sur ce
                            produit.</p>
                        <p>
                            Cette réduction se termine le <u>{response.reduction_end} à 23h59</u>
                            (Heure Europe/Paris, UTC+2).
                        </p>
                        <p>Son prix de base était de {response.price_base_ttc}€ TTC.</p>
                    </>}
                    <p>
                        {
                            response.stock <= 0 ? "Ce produit n'a plus de stock, essayez un autre jours." :
                                response.stock <= 5 ? <>Il ne reste plus que
                                    <strong>{response.stock} unité(s)</strong> de
                                    ce produit en stock !</> : <strong>Ce produit est en stock !</strong>
                        }
                    </p>
                </div>
                <h3>Ajouter dans mon panier</h3>
                <FormWithContext id="addBasketForm" defaultValue={{'quantity': 1}} formError={formError}
                                 onSubmit={handleSubmit}>
                    <SelectField name={"quantity"} labelText={"Quantité souhaité"}>
                        {
                            [...Array(Math.min(3, response.stock)).keys()].map(i =>
                                <option key={i} value={i + 1}>{i + 1}</option>
                            )
                        }
                    </SelectField>
                    <p>Au plus {Math.min(3, response.stock)} unités de ce produit dans le panier.</p>
                    <SubmitButton>Ajouter dans le panier</SubmitButton>
                </FormWithContext>
            </section>}

            <div className="description" dangerouslySetInnerHTML={{__html: response.description}}>
            </div>

            <figure>
                <img src={rule} alt="licence"/>
                <figcaption>Images Licence</figcaption>
            </figure>
        </article>
    </>
}

export default Product;
