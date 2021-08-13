import React, {useEffect, useMemo, useRef, useState} from 'react';
import Link from 'next/link'
import CatalogueFilters from './catalogue_filters';
import {doubleRangeContext} from '../contexts/double_range';
import BoutiqueContainer from './boutique_container';

function Catalogue({response}) {
    let results = useMemo(() => {
        return response?.results
    }, [response])

    const [doubleRange, setDoubleRange] = useState({
        'min_base': null,
        'max_base': null,
        'kwargs_min': 'min_ttc_price',
        'kwargs_max': 'max_ttc_price'
    })

    const isUpdate = useRef(false)

    useEffect(() => {
        setDoubleRange(
            dr => {
                return {
                    ...dr,
                    'min_base': parseFloat(results?.price_exact_ttc__min),
                    'max_base': parseFloat(results?.price_exact_ttc__max)
                }
            }
        )
    }, [results?.price_exact_ttc__min, results?.price_exact_ttc__max])

    return <div className="catalog">
        <nav className="product_categories">
            <h3>Categories</h3>
            <ul>
                <li className={results?.index == null && "is-active"}>
                    <Link href="/"><a>Tous les produit</a></Link>
                </li>

                {results?.filled_category && results.filled_category.map((category, i) => (
                    <li key={i} className={results?.index && results?.index === category?.slug && "is-active"}>
                        <Link href="/"><a>{category?.category} ({category?.products_count__sum})</a></Link>
                    </li>
                ))}
            </ul>
        </nav>
        <doubleRangeContext.Provider value={doubleRange}>
            <CatalogueFilters/>
        </doubleRangeContext.Provider>

        <BoutiqueContainer response={response}/>
    </div>
}

export default Catalogue;
