import React, { useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import DoubleRange from './double_range';
import { useHistory } from 'react-router-dom';


function CatalogueFilters({ query }) {
    let history = useHistory()

    const onClickOrder = useCallback(
        (e, order) => {
            query.set('order', order)
            e.preventDefault()
            history.push({
                search: `?${query.toString()}`
            })
        }, [query, history]
    )

    const order = useMemo(() => {
        const order = query.get('order')
        if (order == 'null') {
            return null
        }
        return order
    }, [query])

    return <div className="filters">
        <nav className="order_filters">
            <ul>
                <li className={order && order == "asc" ? "is-active" : ""}>
                    <a href="" onClick={(e) => onClickOrder(e, "asc")}>
                        Prix croissant
                    </a>
                </li>
                <li className={order && order == "desc" ? "is-active" : ""}>
                    <a href="" onClick={(e) => onClickOrder(e, "desc")}>
                        Prix décroissant
                    </a>
                </li>
                <li className={order === null ? "is-active" : ""}>
                    <a href="" onClick={(e) => onClickOrder(e, null)}>
                        Derniers ajouts
                    </a>
                </li>
            </ul>
        </nav>

        <DoubleRange />
    </div>
}

CatalogueFilters.propTypes = {
    query: PropTypes.object.isRequired,
}

export default CatalogueFilters;
