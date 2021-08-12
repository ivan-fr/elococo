import React from 'react'
import { getUrlSearchParams } from '../utils/url'

export const onDrChange = (doubleRangeContext, history) => {
    return ({ min, max }) => {
    const query = history.query
    query[doubleRangeContext.kwargs_min] = min
    query[doubleRangeContext.kwargs_max] = max
    history.push('?' + getUrlSearchParams(query).toString(), undefined, {shallow:true})
}}

export const doubleRangeContext = React.createContext(
    {'min_base': null, 'max_base': null, 'kwargs_min': 'min_ttc_price', 'kwargs_max': 'max_ttc_price'}
)
