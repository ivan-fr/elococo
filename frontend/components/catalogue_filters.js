import React, { useCallback, useMemo } from 'react';
import DoubleRange from './double_range';
import { useRouter } from 'next/router'
import { getUrlSearchParams } from '../utils/url';

function CatalogueFilters() {
    let router = useRouter()

    const onClickOrder = useCallback(
        (e, order) => {
            e.preventDefault()
            const query = router.query
            query['order'] = order
            router.push('?' + getUrlSearchParams(query).toString())
        }, [router]
    )

    const order = useMemo(() => {
        const query = router.query
        const order = query['order']
        if (!order || order === 'null') {
            return null
        }
        return order
    }, [router])

    return <div className="filters">
        <nav className="order_filters">
            <ul>
                <li className={order && order === "asc" ? "is-active" : undefined}>
                    <a href="" onClick={(e) => onClickOrder(e, "asc")}>
                        Prix croissant
                    </a>
                </li>
                <li className={order && order === "desc" ? "is-active" : undefined}>
                    <a href="" onClick={(e) => onClickOrder(e, "desc")}>
                        Prix décroissant
                    </a>
                </li>
                <li className={order === null ? "is-active" : undefined}>
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
