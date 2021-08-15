import React, {useCallback, useContext, useMemo, useState} from "react";
import {formContext} from "../contexts/form";

export function FormWithContext({id, defaultValue, formError, onSubmit, children}) {
    const [data, setData] = useState(defaultValue)
    const handleChange = useCallback((name, value) => {
        setData(d => {
            return {...d, [name]: value}
        })
    }, [])
    const valueProvider = useMemo(() => {
        return {...data, handleChange, formError}
    }, [data, handleChange, formError])

    const handleSubmit = useCallback((e) => {
        e.preventDefault()
        onSubmit(data)
    }, [onSubmit, data])

    return <formContext.Provider value={valueProvider}>
        <form id={id} onSubmit={handleSubmit} method='POST'>
            {formError && formError.non_field_errors && <ul>
                {formError.non_field_errors.map((textError, i) => <li key={i}>{textError}</li>)}
            </ul>}
            {children}
        </form>
    </formContext.Provider>
}

export function FormField({name, children}) {
    const context = useContext(formContext)
    const handleChange = useCallback(function (e) {
        context.handleChange(e.currentTarget.name, e.currentTarget.value)
    }, [context])

    return <>
        <label htmlFor={name}>
            {children}
        </label>
        {context.formError && context.formError[name] && <ul>
            {context.formError[name].map((textError, i) => <li key={i}>{textError}</li>)}
        </ul>}
        <input type={"text"} name={name} id={name} value={context[name] || ''} onChange={handleChange}/>
    </>
}

export function SelectField({name, labelText, children}) {
    const context = useContext(formContext)
    const handleChange = useCallback(function (e) {
        context.handleChange(e.currentTarget.name, e.currentTarget.value)
    }, [context])

    return <>
        <label htmlFor={name}>
            {labelText}
        </label>
        {context.formError && context.formError[name] && <ul>
            {context.formError[name].map((textError, i) => <li key={i}>{textError}</li>)}
        </ul>}
        <select value={context[name]} name={name} id={name} onChange={handleChange}>
            {children}
        </select>
    </>
}

export function SubmitButton({children}) {
    return <button type="submit">{children}</button>
}