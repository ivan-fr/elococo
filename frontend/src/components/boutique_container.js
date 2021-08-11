import React, { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnnotatedTree } from './annotated_tree'
import { Loading } from './loading'
import PropTypes from 'prop-types';


function BoutiqueContainer({ mainReponse, subResponse }) {
    let [response, setResponse] = useState(mainReponse)

    useEffect(() => {
        switch (subResponse.isLoading) {
            case false:
                setResponse(subResponse)
                break;
        }
    }, [subResponse])

    let results = useMemo(() => {
        return response.data?.results
    }, [response.data])

    return <>
        <div id="boutique-container" className={results?.filter_list && "with_filters"}>
            <div id="boutique">
                {subResponse.isLoading == false && results?.related_products ? results.related_products.map((product, i) => (
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
                )) : <Loading />}
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
    </>
}

BoutiqueContainer.propTypes = {
    mainReponse: PropTypes.object.isRequired,
    subResponse: PropTypes.object.isRequired,
}

export default BoutiqueContainer;
