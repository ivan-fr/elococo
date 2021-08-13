import React, {useCallback, useContext, useEffect, useLayoutEffect, useMemo, useRef, useState} from 'react';
import {useRouter} from 'next/router'
import {doubleRangeContext} from '../contexts/double_range';
import {getUrlSearchParams} from '../utils/url';

function linear(start, end, x) {
    let a = (end - start);
    return x * a + start;
}

function reverse_linear(start, end, r) {
    let a = (end - start);
    return (r - start) / a;
}

function DoubleRange() {
    const {min_base, max_base, kwargs_min, kwargs_max} = useContext(doubleRangeContext)
    const zIndex = useRef(10)
    const history = useRouter()

    // ref for DOM
    const dr = useRef(null)
    const dr_witness = useRef(null)
    const box_left = useRef(null)
    const box_right = useRef(null)

    const dr_main = useRef(null)
    const dr_value_left = useRef(null)
    const dr_value_right = useRef(null)

    // ref for functionnality
    const limitQuotient = useRef([null, null])
    const percentage_ = useRef([0, 0])
    const min = useRef(min_base)
    const max = useRef(max_base)
    const minFetch = useRef(min_base)
    const maxFetch = useRef(max_base)

    const direction = useRef(null)
    const tMinusOnePageX = useRef(null)
    const dirMouse = useRef(null)

    const limitMax = useRef(null)
    const start = useRef(null)
    const end = useRef(null)

    const box = useRef(null)
    const isMount = useRef(false)

    const [refresh, setRefresh] = useState(false)

    const currentsCallback = useRef({
        'move': null, 'up': null
    })

    const delta_value = useMemo(() => max_base - min_base, [max_base, min_base])

    const update_bar = useCallback(function update_bar() {
        let new_with = Math.abs(
            (
                box_right.current.getBoundingClientRect().right
                - box_left.current.getBoundingClientRect().left
                - box_left.current.getBoundingClientRect().width
            )
        );
        let new_left = (
            box_left.current.getBoundingClientRect().left
            - dr_witness.current.getBoundingClientRect().left
            + box_left.current.getBoundingClientRect().width
        );
        dr.current.style.width = `${new_with}px`;
        dr.current.style.left = `${new_left}px`;
    }, [])

    useEffect(() => {
        window.addEventListener('resize', update_bar);
        return () => window.removeEventListener('resize', update_bar)
    }, [update_bar])

    const refreshLeft = useCallback((min_, max, min_base, max_base) => {
        let limitMax = reverse_linear(min_base, max_base, max - 2);

        if (isNaN(limitMax) || !isFinite(limitMax)) {
            return [undefined, 0]
        }

        const base_percentage = Math.max(
            0,
            Math.min(
                reverse_linear(min_base, max_base, min_), limitMax
            )
        );
        const starter = min_base;
        const value = linear(min_base, max_base, base_percentage);
        const function_quotient = Math.floor
        const function_quotient_2 = Math.ceil

        const quotient_relative = Math.sign(
            function_quotient_2((value - starter) / 2)
        ) * function_quotient(Math.abs(value - starter) / 2);

        limitQuotient.current[0] = quotient_relative

        let value_target = min_base + 2 * quotient_relative;
        let back_base_percentage = reverse_linear(min_base, max_base, value_target);

        let percentage = Math.max(0, Math.min(back_base_percentage, limitMax));

        let distance_value = linear(min_base, max_base, percentage);

        distance_value = (Math.round((distance_value + Number.EPSILON) * 100) / 100)

        return [distance_value, percentage]
    }, [])

    const refreshRight = useCallback((min, max_, min_base, max_base) => {
        let limitMax = reverse_linear(max_base, min_base, min + 2)

        if (isNaN(limitMax) || !isFinite(limitMax)) {
            return [undefined, 0]
        }

        const base_percentage = Math.max(
            0,
            Math.min(
                reverse_linear(max_base, min_base, max_), limitMax
            )
        )
        const starter = max_base;
        const value = linear(max_base, min_base, base_percentage);
        const function_quotient = Math.floor
        const function_quotient_2 = Math.floor

        const quotient_relative = Math.sign(
            function_quotient_2((value - starter) / 2)
        ) * function_quotient(Math.abs(value - starter) / 2);

        limitQuotient.current[1] = quotient_relative

        let value_target = max_base + 2 * quotient_relative;
        let back_base_percentage = reverse_linear(max_base, min_base, value_target);

        let percentage = Math.max(0, Math.min(back_base_percentage, limitMax));

        let distance_value = linear(max_base, min_base, percentage);
        distance_value = (Math.round((distance_value + Number.EPSILON) * 100) / 100)

        return [distance_value, percentage]
    }, [])

    useLayoutEffect(() => {
        if (!history.query[kwargs_max] || !history.query[kwargs_min]) {
            console.log("do")
            percentage_.current = [0, 0]
            min.current = null
            max.current = null
            limitQuotient.current = [null, null]
        }
    }, [history, kwargs_max, kwargs_min])

    useLayoutEffect(() => {
        if (!isMount.current) {
            isMount.current = true
            return
        }

        const query = history.query
        const pMin = parseFloat(query[kwargs_min])
        const pMax = parseFloat(query[kwargs_max])

        let prevMin = isNaN(pMin) ? min_base : pMin
        let prevMax = isNaN(pMax) ? max_base : pMax
        console.log(prevMin, min.current, max.current)

        let [nextMin, perLeft] = refreshLeft(prevMin, prevMax, min_base, max_base)
        let [nextMax, perRight] = refreshRight(prevMin, prevMax, min_base, max_base)

        console.log(prevMin, min.current, max.current, nextMin, nextMax)

        if (Math.abs(prevMin - nextMin) < 1e-2 && Math.abs(prevMax - nextMax) < 1e-2) {
            minFetch.current = min.current = nextMin
            maxFetch.current = max.current = nextMax
            percentage_.current[0] = perLeft
            percentage_.current[1] = perRight
            setRefresh(r => !r)
        } else {
            if (min.current && max.current) {
                query[kwargs_min] = min.current
                query[kwargs_max] = max.current
                history.push('?' + getUrlSearchParams(query).toString())
            }
        }

        return () => {
            isMount.current = false
        }
    }, [min_base, max_base, kwargs_max, kwargs_min, refreshRight, refreshLeft, history])

    useLayoutEffect(() => {
        update_bar()
    }, [refresh, update_bar])

    const move = useCallback(
        (event) => {
            let dir_mouse;

            if (tMinusOnePageX.current !== null) {
                if (event.pageX - tMinusOnePageX.current > 0) {
                    dir_mouse = 0
                } else if (event.pageX - tMinusOnePageX.current < 0) {
                    dir_mouse = 1
                } else {
                    tMinusOnePageX.current = event.pageX;
                    return;
                }
            } else {
                tMinusOnePageX.current = event.pageX;
                return;
            }

            let justChange = dirMouse.current !== dir_mouse;

            dirMouse.current = dir_mouse;
            tMinusOnePageX.current = event.pageX;

            let start_bis, end_bis;
            if (direction.current !== dir_mouse) {
                [start_bis, end_bis] = [end.current, start.current]
            } else {
                [start_bis, end_bis] = [start.current, end.current]
            }

            let base_percentage, function_quotient, function_quotient_2;
            if (direction.current === 1) {
                function_quotient = (dir_mouse === 1) ? Math.floor : Math.ceil;
                function_quotient_2 = (dir_mouse === 1) ? Math.floor : Math.ceil;
                base_percentage = Math.max(
                    0,
                    Math.min(
                        (
                            dr_main.current.getBoundingClientRect().right
                            - event.pageX
                        ) / dr_main.current.getBoundingClientRect().width,
                        limitMax.current)
                );
            } else {
                function_quotient = (dir_mouse === 0) ? Math.floor : Math.ceil;
                function_quotient_2 = (dir_mouse === 0) ? Math.ceil : Math.floor;
                base_percentage = Math.max(
                    0,
                    Math.min(
                        (
                            event.pageX - dr_main.current.getBoundingClientRect().left
                        ) / dr_main.current.getBoundingClientRect().width, limitMax.current)
                );
            }

            let starter;
            if (direction.current === 1) {
                if (dirMouse.current === 1) {
                    starter = max_base;
                } else {
                    starter = max_base - Math.floor(delta_value / 2) * 2;
                }
            } else {
                if (dirMouse.current === 1) {
                    starter = min_base + Math.floor(delta_value / 2) * 2;
                } else {
                    starter = min_base;
                }
            }

            let value = linear(start_bis, end_bis, base_percentage);
            let quotient_relative = Math.sign(
                function_quotient_2((value - starter) / 2)
            ) * function_quotient(Math.abs(value - starter) / 2);

            if (direction.current !== dir_mouse) {
                quotient_relative *= -1;
            }

            let func;
            if (direction.current === 1) {
                if (dir_mouse === 1) {
                    func = Math.max
                } else {
                    func = Math.min
                }
            } else {
                if (dir_mouse === 1) {
                    func = Math.min
                } else {
                    func = Math.max
                }
            }

            let sign = Math.sign(quotient_relative);
            if (sign === 0) {
                if (direction.current === 1) {
                    sign = -1;
                } else {
                    sign = 1
                }
            }

            if (justChange === true) {
                limitQuotient.current[direction.current] = func(Math.abs(quotient_relative), Math.abs(limitQuotient.current[direction.current])) * sign;
            }

            if (limitQuotient.current[direction.current] !== null) {
                quotient_relative = func(Math.abs(quotient_relative), Math.abs(limitQuotient.current[direction.current])) * sign;
            }

            limitQuotient.current[direction.current] = quotient_relative

            let value_target = start.current + 2 * quotient_relative;
            let back_base_percentage = reverse_linear(start.current, end.current, value_target);

            let percentage = Math.max(0, Math.min(back_base_percentage, limitMax.current));

            let distance_value = linear(start.current, end.current, percentage);

            if (direction.current === 1) {
                max.current = (Math.round((distance_value + Number.EPSILON) * 100) / 100)
            } else {
                min.current = (Math.round((distance_value + Number.EPSILON) * 100) / 100)
            }
            percentage_.current[direction.current] = percentage

            setRefresh(r => !r)
        }, [delta_value, max_base, min_base]
    )

    const cleanEvent = useCallback(() => {
        if (currentsCallback.current.move) {
            window.removeEventListener('mousemove', currentsCallback.current.move)
            currentsCallback.current.move = null
        }
        if (currentsCallback.current.up) {
            window.removeEventListener('mouseup', currentsCallback.current.up)
            currentsCallback.current.up = null
        }
    }, [])

    const upCallback = useCallback(
        () => {
            cleanEvent()
            document.body.style.cursor = null;
            document.body.style.userSelect = null;
            box_right.current.style.backgroundColor = null;
            box_left.current.style.backgroundColor = null;

            if (min.current !== minFetch.current || max.current !== maxFetch.current) {
                minFetch.current = min.current ? min.current : min_base
                maxFetch.current = max.current ? max.current : max_base

                const query = history.query
                query[kwargs_min] = minFetch.current
                query[kwargs_max] = maxFetch.current
                history.push('?' + getUrlSearchParams(query).toString())
            }
        }, [history, cleanEvent, kwargs_min, kwargs_max, min_base, max_base])

    const downCallback = useCallback(
        (event) => {
            cleanEvent()
            dirMouse.current = null
            tMinusOnePageX.current = null

            event.currentTarget.parentElement.style.zIndex = `${zIndex.current}`;
            zIndex.current++;
            document.body.style.cursor = "move";
            document.body.style.userSelect = "none";

            currentsCallback.current.move = move
            currentsCallback.current.up = upCallback

            window.addEventListener("mousemove", currentsCallback.current.move);
            window.addEventListener("mouseup", currentsCallback.current.up);
        }, [move, upCallback, cleanEvent])

    const leftDown = useCallback((e) => {
        direction.current = 0
        start.current = min_base;
        end.current = max_base;
        box.current = box_left.current

        const max_ = max.current ? max.current : end.current

        limitMax.current = reverse_linear(start.current, end.current, max_ - 2);
        downCallback(e)
    }, [downCallback, max_base, min_base])

    const rightDown = useCallback((e) => {
        direction.current = 1
        start.current = max_base
        end.current = min_base;
        box.current = box_right.current

        const min_ = min.current ? min.current : end.current

        limitMax.current = reverse_linear(start.current, end.current, min_ + 2);
        downCallback(e)
    }, [downCallback, min_base, max_base])

    return <nav className="range_filter">
        <ul key={refresh}>
            <li>
                <div ref={dr_value_left} className="dr_value_left text-left">
                    {
                        min_base && min.current ?
                            (
                                min.current > min_base ? min.current.toFixed(2) : min_base.toFixed(2)
                            ) : min_base && min_base.toFixed(2)
                    } € {min.current} {min_base}
                </div>
                <div ref={dr_main} className="dr_main">
                    <div
                        style={{'left': `max(0px, ${percentage_.current[0] * 100}% - ${box_right.current ? box_right.current.getBoundingClientRect().width : 0}px)`}}
                        className="dr_wrapper">
                        <div ref={box_left} onMouseDown={leftDown} className="dr_box"/>
                    </div>
                    <div
                        style={{'right': `max(0px, ${percentage_.current[1] * 100}% - ${box_left.current ? box_left.current.getBoundingClientRect().width : 0}px)`}}
                        className="dr_wrapper">
                        <div ref={box_right} onMouseDown={rightDown} className="dr_box"/>
                    </div>
                    <div ref={dr_witness} className="double_range_temoin">
                    </div>
                    <div ref={dr} className="double_range">
                    </div>
                </div>
                <div ref={dr_value_right} className="dr_value_right text-right">
                    {
                        max_base && max.current ?
                            (
                                max.current < max_base ? max.current.toFixed(2) : max_base.toFixed(2)
                            ) : max_base && max_base.toFixed(2)
                    } €
                </div>
            </li>
        </ul>
    </nav>
}

export default DoubleRange;
