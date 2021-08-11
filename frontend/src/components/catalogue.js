import React, { useCallback, useLayoutEffect, useMemo, useState } from 'react';
import { useSimpleFetch } from '../hooks/fetcher';
import { Loading } from './loading';
import { Link, useHistory, useLocation } from 'react-router-dom'
import { AnnotatedTree } from './annotated_tree';
import "../css/double_range.css"
import CatalogueFilters from './catalogue_filters';
import { doubleRangeContext, onChange } from '../contexts/double_range';

function Catalogue() {
    let history = useHistory()
    let { search } = useLocation()
    const query = useMemo(() => new URLSearchParams(search), [search]);  

    const response = useSimpleFetch('catalogue_api:product-list', [], query)

    const [doubleRange, setDoubleRange] = useState({
        'min_base': null, 'max_base': null, 'kwargs_min': 'min_ttc_price', 'kwargs_max': 'max_ttc_price'
    })

    let results = useMemo(() => {
        return response.data?.results
    }, [response.data])

    useLayoutEffect(() => {
        if (response.isLoading === false) {
            setDoubleRange(
                dr => {
                    return {
                        ...dr,
                        'min_base': results.price_exact_ttc__min,
                        'max_base': results.price_exact_ttc__max
                    }
                }
            )
        }
    }, [response.isLoading, results?.price_exact_ttc__min, results?.price_exact_ttc__max])

    // eslint-disable-next-line react-hooks/exhaustive-deps
    let onDoubleRangeChange = useCallback(onChange(doubleRange, history, query), [])
    const doubleRangeValue = useMemo(() => {
        return { ...doubleRange, 'change': onDoubleRangeChange }
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
                            <Link to="/">Tous les produit</Link>
                        </li>

                        {results?.filled_category && results.filled_category.map((category, i) => (
                            <li key={i} className={results?.index && results.index == category.slug && "is-active"}>
                                <Link to="/">{category.category} ({category.products_count__sum})</Link>
                            </li>
                        ))}
                    </ul>
                </nav>
                <doubleRangeContext.Provider value={doubleRangeValue}>
                    <CatalogueFilters query={query} />
                </doubleRangeContext.Provider>

                <div id="boutique-container" className={results?.filter_list && "with_filters"}>
                    <div id="boutique">
                        {results?.related_products && results.related_products.map((product, i) => (
                            <article key={i}>
                                <h3>{product.name}</h3>

                                <figure className="hover_figure">
                                    <Link to="/">
                                        <img src={product.productimage_set[0].image}
                                            alt={'product' + i} />

                                        {product.effective_reduction > 0 &&
                                            <div className="info_reduction">
                                                -{product.effective_reduction}%
                                            </div>
                                        }
                                        <div className="info_price">
                                            {product.price_exact_ttc}€ TTC
                                        </div>
                                        <figcaption>
                                            {product.name}
                                        </figcaption>
                                    </Link>
                                </figure>
                            </article>
                        ))}
                    </div>

                    {results?.filter_list && (
                        <section className="product_categories_right">
                            <h2>Filtres associés</h2>
                            <AnnotatedTree tree={results.filter_list} selected_category={results.selected_category} />
                        </section>
                    )}
                </div>
                {(response.data?.next || response.data?.previous) && <nav id="boutique_pagination">
                    <ul className="pagination">
                        {response.data?.previous && <>
                            <li className="page-item">
                                <span className="page-link">
                                    <Link to="/">
                                        Prec
                                    </Link>
                                </span>
                            </li>
                        </>}
                        {response.data?.next && <>
                            <li className="page-item">
                                <span className="page-link">
                                    <Link to="/">
                                        Suiv
                                    </Link>
                                </span>
                            </li>
                        </>}
                    </ul>
                </nav>}
            </div>
        default:
            return <div className="catalog">Envoie de la requête.</div>
    }
}

export default Catalogue;
