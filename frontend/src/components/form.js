import React, {useCallback, useContext, useEffect, useMemo, useRef, useState} from "react";
import {formContext} from "../contexts/form";


export function ErrorNonFieldError() {
    const context = useContext(formContext)
    const formError = useMemo(() => context.formError, [context])

    if (context.many) {
        return <>{formError && formError.map((fields, i) => <ul key={i}>
            {fields.non_field_errors && fields.non_field_errors.map((textError, i) => <li key={i}>{textError}</li>)}
        </ul>)}</>
    }

    return <>{formError && formError.non_field_errors && <ul>
        {formError.non_field_errors.map((textError, i) => <li key={i}>{textError}</li>)}
    </ul>}</>
}


export function FieldError({name, index = 0}) {
    const context = useContext(formContext)

    if (context.many) {
        const match = name.match(new RegExp('^[^_]+_[^_]+_(.+)$'))[1]
        return <>{context.formError && context.formError[index] && context.formError[index][match] && <ul>
            {context.formError[index][match].map((textError, i) => <li key={i}>{textError}</li>)}
        </ul>}</>
    }

    return <>{context.formError && context.formError[name] && <ul>
        {context.formError[name].map((textError, i) => <li key={i}>{textError}</li>)}
    </ul>}</>
}


export function FormWithContext({id, defaultValue, formError, onSubmit, many = false, children}) {
    const [defaultValues_, setDefaultValues_] = useState(defaultValue)
    const handleChange = useCallback((name, value) => {
        setDefaultValues_(defaults => {
            return {...defaults, [name]: value}
        })
    }, [])
    const valueProvider = useMemo(() => {
        return {...defaultValues_, handleChange, formError, many}
    }, [many, defaultValues_, handleChange, formError])

    const handleSubmit = useCallback((e) => {
        e.preventDefault()
        onSubmit(defaultValues_)
    }, [onSubmit, defaultValues_])

    return <formContext.Provider value={valueProvider}>
        <form id={id} onSubmit={handleSubmit} method='POST'>
            <ErrorNonFieldError many={many}/>
            {children}
        </form>
    </formContext.Provider>
}

export function InputTextField({name, index = 0, children}) {
    const context = useContext(formContext)
    const handleChange = useCallback(function (e) {
        context.handleChange(e.currentTarget.name, e.currentTarget.value)
    }, [context])

    return <>
        <label htmlFor={name}>
            {children}
        </label>
        <FieldError name={name} index={index}/>
        <input type={"text"} name={name} id={name} value={context[name] || ''} onChange={handleChange}/>
    </>
}

export function SelectField({name, labelText, index = 0, children}) {
    const context = useContext(formContext)
    const handleChange = useCallback(function (e) {
        context.handleChange(e.currentTarget.name, e.currentTarget.value)
    }, [context])

    return <>

        {labelText && <label htmlFor={name}>
            {labelText}
        </label>}
        <FieldError name={name} index={index}/>

        <select value={context[name]} name={name} id={name} onChange={handleChange}>
            {children}
        </select>
    </>
}

export function CheckBoxField({name, index = 0, children}) {
    const context = useContext(formContext)
    const handleChange = useCallback(function (e) {
        context.handleChange(e.currentTarget.name, e.currentTarget.checked)
    }, [context])

    return <>
        {children && <label htmlFor={name}>
            {children}
        </label>}
        <FieldError name={name} index={index}/>

        <input type="checkbox" checked={context[name]} name={name} id={name} onChange={handleChange}/>
    </>
}

export function SubmitButton({children, ifChange}) {
    const context = useContext(formContext)
    const isMount = useRef(false)
    const [hide, setHide] = useState(ifChange)

    useEffect(() => {
        if (isMount.current) {
            setHide(false)
        }
        isMount.current = true
    }, [context])

    if (hide) {
        return <></>
    }

    return <button type="submit">{children}</button>
}