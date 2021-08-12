import React, { useCallback, useMemo } from 'react';
import DoubleRange from './double_range';
import { useRouter } from 'next/router'
import { getUrlSearchParams } from '../utils/url';

function CatalogueFilters() {
    let history = useRouter()

    const onClickOrder = useCallback(
        (e, order) => {
            e.preventDefault()
            const query = history.query
            query['order'] = order
            history.push('?' + getUrlSearchParams(query).toString(), undefined, {shallow:true})
        }, [history]
    )

    const order = useMemo(() => {
        const query = history.query
        const order = query['order']
        if (order == 'null') {
            return null
        }
        return order
    }, [history])

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

export default CatalogueFilters;
