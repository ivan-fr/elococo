import React, { useState } from 'react';
import { useSimpleFetch } from '../hooks/fetcher';
import { Loading } from './loading';
import { Link } from 'react-router-dom'
import "../css/double_range.css"

function Catalogue() {
    const [isLoading, setIsLoading] = useState(null);
    const [catalogue, setCatalogue] = useState(null);
    const [error, setError] = useState(null);
    useSimpleFetch('catalogue_api:product-list', [], setCatalogue, setError, setIsLoading)

    if (isLoading == null) {
        return <div className="catalog">Envoie de la requête.</div>
    }

    let results = catalogue?.results

    switch (isLoading) {
        case true:
            return <Loading />
        case false:
            if (error) {
                return <div className="catalog">Erreur lors du chargement.</div>
            }
            return <div className="catalog">
                <nav className="product_categories">
                    <h3>Categories</h3>
                    <ul>
                        <li className={results?.index && "is-active"}>
                            <Link to="/">Tous les produit</Link>
                        </li>
                    </ul>

                    {results?.filled_category && results.filled_category.map((i, category) => (
                        <li key={i} className={results?.index && "is-active"}>
                            <Link to="/">{category.category} ({category.products_count__sum}))</Link>
                        </li>
                    ))}
                </nav>

                <div id="boutique-container" className={results?.filter_list && "with_filters"}>
                    <div id="boutique">
                        {results?.related_products && results.related_products.map((i, product) => (
                            <article key={i}>
                                <h3>{product.name}</h3>

                                <figure className="hover_figure">
                                    <Link to="/">
                                        <img src="{{ product_image.image.url }}"
                                            alt="product_{{ forloop.counter }}_{{ product.name }}" />

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

                    {result?.filter_list && (
                        <section className="product_categories_right">
                            <h2>Filtres associés</h2>

                            {results.filter_list.map(filter => (
                                <>
                                    {filter.annotation.open ? <ul>
                                        <li className={results?.selected_category == filter.category.slug ? "active" : ""}>
                                            :
                                        </li>
                                        <li className={results?.selected_category == filter.category.slug ? "active" : ""}>
                                    }

                                            <Link to="/">{filter.category.category}({filter.category.products_count__sum})</Link>

                                            {filter.annotation.close.map(_ => </li></ul>)}
                                </>
                            ))}
                        </section>
                    )}
                </div>
            </div>
        default:
            return <div className="catalog">Envoie de la requête.</div>
    }
}

export default Catalogue;
