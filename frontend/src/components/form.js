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


export function FieldError({name, index = null}) {
    const context = useContext(formContext)

    if (index !== null) {
        const match = name.match(new RegExp('^([^_]+)_[^_]+_(.+)$'))

        let list;
        if (context.many) {
            list = context.formError
                && context.formError[match[2]]
                && context.formError[index][match[2]]
        } else {
            list = context.formError
                && context.formError[match[1]]
                && context.formError[match[1]][index]
                && context.formError[match[1]][index][match[2]]
        }

        return <>{list && <ul>
            {list.map((textError, i) => <li key={i}>{textError}</li>)}
        </ul>}</>
    }

    return <>{context.formError && context.formError[name] && <ul>
        {context.formError[name].map((textError, i) => <li key={i}>{textError}</li>)}
    </ul>}</>
}


export function FormWithContext({id, className, defaultValue, onSubmit, formError = null, many = false, children}) {
    const [defaultValues_, setDefaultValues_] = useState(defaultValue)
    const handleChange = useCallback((name, value) => {
        setDefaultValues_(defaults => {
            if (defaults && defaults.submit) {
                defaults.submit = false
            }

            return {...defaults, [name]: value}
        })
    }, [])

    const handleSubmit = useCallback((e) => {
        e.preventDefault()
        onSubmit(defaultValues_)
        handleChange("submit", true)
    }, [onSubmit, handleChange, defaultValues_])

    const valueProvider = useMemo(() => {
        return {"submit": false, ...defaultValues_, handleChange, formError, many}
    }, [many, defaultValues_, handleChange, formError])

    return <formContext.Provider value={valueProvider}>
        <form id={id} className={className} onSubmit={handleSubmit} method='POST'>
            <ErrorNonFieldError/>
            {children}
        </form>
    </formContext.Provider>
}

export function InputTextField({name, index = null, children}) {
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

export function SelectField({name, labelText, index = null, children}) {
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

export function CheckBoxField({name, index = null, children}) {
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

export function SubmitButton({children, ifChange = false}) {
    const context = useContext(formContext)
    const isMount = useRef(false)
    const [hide, setHide] = useState(ifChange)

    useEffect(() => {
        if (isMount.current) {
            setHide(() => {
                return context.submit && ifChange;
            })
        }
        isMount.current = true
    }, [context, ifChange])

    if (hide) {
        return <></>
    }

    return <button type="submit">{children}</button>
}