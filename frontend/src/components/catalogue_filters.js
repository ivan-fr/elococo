import React, { useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import DoubleRange from './double_range';
import { useHistory } from 'react-router-dom';


function CatalogueFilters({ query }) {
    let history = useHistory()

    const onClickOrder = useCallback(
        (order) => {
            query.set('order', order)
            return (e) => {
                e.preventDefault()
                history.push({
                    search: `?${query.toString()}`
                })
            }
        }, [query, history]
    )

    const order = useMemo(() => query.get('order'), [query])

    return <div className="filters">
        <nav className="order_filters">
            <ul>
                <li className={order && order == "asc" ? "is-active" : ""}>
                    <a onClick={onClickOrder("asc")}>
                        Prix croissant
                    </a>
                </li>
                <li className={order && order == "desc" ? "is-active" : ""}>
                    <a onClick={onClickOrder("desc")}>
                        Prix décroissant
                    </a>
                </li>
                <li className={order && order == null ? "is-active" : ""}>
                    <a onClick={onClickOrder(null)}>
                        Derniers ajouts
                    </a>
                </li>
            </ul>
        </nav>

        <DoubleRange />
    </div>
}

CatalogueFilters.propTypes = {
    query: PropTypes.func.isRequired,
}

export default CatalogueFilters;
