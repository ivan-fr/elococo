import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useFetchOnlyDepsFromName, useSubFetch } from '../hooks/fetcher';
import { Loading } from './loading';
import Link from 'next/link'
import { useRouter } from 'next/router'
import CatalogueFilters from './catalogue_filters';
import { doubleRangeContext, onDrChange } from '../contexts/double_range';
import BoutiqueContainer from './boutique_container';

function Catalogue() {
    let history = useRouter()

    const response = useFetchOnlyDepsFromName('catalogue_api:product-list', [], history.query)
    const subResponse = useSubFetch('catalogue_api:product-list', [], response.isLoading, history.query)

    const [doubleRange, setDoubleRange] = useState({
        'min_base': null, 'max_base': null, 'kwargs_min': 'min_ttc_price', 'kwargs_max': 'max_ttc_price'
    })

    let results = useMemo(() => {
        return response.data?.results
    }, [response.data])

    useEffect(() => {
        if (response.isLoading === false) {
            setDoubleRange(
                dr => {
                    return {
                        ...dr,
                        'min_base': parseFloat(results?.price_exact_ttc__min),
                        'max_base': parseFloat(results?.price_exact_ttc__max)
                    }
                }
            )
        }
    }, [response.isLoading, results?.price_exact_ttc__min, results?.price_exact_ttc__max])

    // eslint-disable-next-line react-hooks/exhaustive-deps
    let onDoubleRangeChange = useCallback(onDrChange(doubleRange, history), [doubleRange, history])
    const doubleRangeValue = useMemo(() => {
        return { ...doubleRange, 'drChange': onDoubleRangeChange }
    }, [doubleRange, onDoubleRangeChange])

    if (response.isLoading == null) {
        return <div className="catalog">Envoie de la requête.</div>
    }

    switch (response.isLoading) {
        case true:
            return <Loading />
        case false:
            if (response.error) {
                return <div className="catalog">Erreur lors du chargement.</div>
            }
            return <div className="catalog">
                <nav className="product_categories">
                    <h3>Categories</h3>
                    <ul>
                        <li className={results?.index == null && "is-active"}>
                            <Link href="/"><a>Tous les produit</a></Link>
                        </li>

                        {results?.filled_category && results.filled_category.map((category, i) => (
                            <li key={i} className={results?.index && results.index == category.slug && "is-active"}>
                                <Link href="/"><a>{category.category} ({category.products_count__sum})</a></Link>
                            </li>
                        ))}
                    </ul>
                </nav>
                <doubleRangeContext.Provider value={doubleRangeValue}>
                    <CatalogueFilters />
                </doubleRangeContext.Provider>

                <BoutiqueContainer mainReponse={response} subResponse={subResponse} />
            </div>
        default:
            return <div className="catalog">Envoie de la requête.</div>
    }
}

export default Catalogue;
