import React from 'react'

export const onDrChange = (doubleRangeContext, history, query) => {
    return ({ min, max }) => {
    query.set(doubleRangeContext.kwargs_min, min)
    query.set(doubleRangeContext.kwargs_max, max)
    history.push({
        search: `?${query.toString()}`
    })
}}

export const doubleRangeContext = React.createContext(
    {'min_base': null, 'max_base': null, 'kwargs_min': 'min_ttc_price', 'kwargs_max': 'max_ttc_price'}
)
