import React, {useEffect, useMemo, useState} from 'react';
import CatalogueOrder from './catalogue_filters';
import BoutiqueContainer from './boutique_container';
import DoubleRange from "./double_range";
import {Loading} from "./loading";
import axios from "axios";
import {get_route_with_args, get_url} from "../utils/url";
import {Link, useLocation, useParams} from "react-router-dom";

function Catalogue() {
    const [response, setResponse] = useState(null)
    const [isError, setIsError] = useState(false)
    const {search} = useLocation()
    let {slug} = useParams();
    let results = useMemo(() => {
        return response?.results
    }, [response])

    useEffect(() => {
        const fetchData = async () => {
            try {
                let path
                if (!slug) {
                    path = get_route_with_args('catalogue_api:product-list', [])
                } else {
                    path = get_route_with_args('catalogue_api:product-list-category', [slug])
                }

                const url = get_url(path, search)
                const res = await axios(url.href)
                setResponse(res.data)
                setIsError(false)
            } catch (error) {
                setIsError(true)
            }
        }

        fetchData().then(() => null)
    }, [search, slug])

    if (isError) {
        return <div className="catalog">Erreur lors du chargement.</div>
    }

    if (response === null) {
        return <Loading/>
    }

    return <div className="catalog">
        <nav className="product_categories">
            <h3>Categories</h3>
            <ul>
                <li className={results?.index == null ? "is-active" : undefined}>
                    <Link to="/">Tous les produit</Link>
                </li>

                {results?.filled_category && results.filled_category.map((category, i) => (
                    <li key={i} className={results?.index && results?.index === category?.slug && "is-active"}>
                        <Link to={`/category/${category.slug}`}>
                            {category.category} ({category.products_count__sum})
                        </Link>
                    </li>
                ))}
            </ul>
        </nav>
        <div className="filters">
            <CatalogueOrder/>
            <DoubleRange kwargs_min='min_ttc_price' kwargs_max='max_ttc_price'
                         min_base={parseFloat(results.price_exact_ttc__min)}
                         max_base={parseFloat(results.price_exact_ttc__max)}/>
        </div>

        <BoutiqueContainer response={response}/>
    </div>
}

export default Catalogue;
