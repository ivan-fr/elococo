/* eslint-disable no-unused-vars */
import React, { useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useHistory, useLocation } from 'react-router-dom';
import { doubleRangeContext } from '../contexts/double_range';


function linear(start, end, x) {
    let a = (end - start);
    return x * a + start;
}

function reverse_linear(start, end, r) {
    let a = (end - start);
    return (r - start) / a;
}

function DoubleRange() {
    const { min_base, max_base, drChange, kwargs_min, kwargs_max } = useContext(doubleRangeContext)
    const zIndex = useRef(10)
    let history = useHistory()
    let { search } = useLocation()
    const query = useMemo(() => new URLSearchParams(search), [search]);

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
    const min = useRef(min_base)
    const max = useRef(max_base)
    const minFetch = useRef(min_base)
    const maxFetch = useRef(max_base)

    const direction = useRef(null)
    const tMinusOnePagex = useRef(null)
    const dirMouse = useRef(null)

    const limitMax = useRef(null)
    const directionSTR = useRef(null)
    const start = useRef(null)
    const end = useRef(null)

    const box = useRef(null)
    const isMount = useRef(false)

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

    const refreshLeft = useCallback(() => {
        limitMax.current = reverse_linear(min_base, max_base, max.current - 2);

        const base_percentage = Math.max(
            0,
            Math.min(
                reverse_linear(min_base, max_base, min.current), limitMax.current
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

        let percentage = Math.max(0, Math.min(back_base_percentage, limitMax.current));

        let distance_value = linear(min_base, max_base, percentage);

        distance_value = (Math.round((distance_value + Number.EPSILON) * 100) / 100)
        min.current = distance_value
        dr_value_left.current.textContent = `${distance_value.toFixed(2)} €`;

        box_left.current.parentElement.style.setProperty(
            'left', `max(0px, ${percentage * 100}% - ${box_right.current.getBoundingClientRect().width}px)`
        );

        update_bar()
    }, [min_base, max_base, update_bar])

    const refreshRight = useCallback(() => {
        limitMax.current = reverse_linear(max_base, min_base, min.current + 2);

        const base_percentage = Math.max(
            0,
            Math.min(
                reverse_linear(max_base, min_base, max.current), limitMax.current
            )
        );
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

        let percentage = Math.max(0, Math.min(back_base_percentage, limitMax.current));

        let distance_value = linear(max_base, min_base, percentage);

        distance_value = (Math.round((distance_value + Number.EPSILON) * 100) / 100)
        max.current = distance_value
        dr_value_right.current.textContent = `${distance_value.toFixed(2)} €`;

        box_right.current.parentElement.style.setProperty(
            'right', `max(0px, ${percentage * 100}% - ${box_right.current.getBoundingClientRect().width}px)`
        );

        update_bar()
    }, [min_base, max_base, update_bar])

    useEffect(() => {
        if (!isMount.current) {
            isMount.current = true
            return
        }

        min.current = parseFloat(query.get(kwargs_min)) || min_base
        max.current = parseFloat(query.get(kwargs_max)) || max_base
        refreshLeft()
        refreshRight()

        query.set(kwargs_min, min.current)
        query.set(kwargs_max, max.current)
        history.push({
            search: `?${query.toString()}`
        })

        minFetch.current = min.current
        maxFetch.current = max.current
    }, [min_base, max_base, query, kwargs_max, kwargs_min, refreshRight, refreshLeft, history])

    const move = useCallback(
        (event) => {
            let dir_mouse;

            if (tMinusOnePagex.current !== null) {
                if (event.pageX - tMinusOnePagex.current > 0) {
                    dir_mouse = 0
                } else if (event.pageX - tMinusOnePagex.current < 0) {
                    dir_mouse = 1
                } else {
                    tMinusOnePagex.current = event.pageX;
                    return;
                }
            } else {
                tMinusOnePagex.current = event.pageX;
                return;
            }

            let justChange = dirMouse.current !== dir_mouse;

            dirMouse.current = dir_mouse;
            tMinusOnePagex.current = event.pageX;

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

            if (dir_mouse !== direction.current) {
                sign *= -1
            }

            let next_value_target = start.current + 2 * (quotient_relative + sign);
            let next_back_base_percentage = reverse_linear(start.current, end.current, next_value_target);
            let value_target = start.current + 2 * quotient_relative;
            let back_base_percentage = reverse_linear(start.current, end.current, value_target);

            if (isNaN(back_base_percentage)) {
                box_right.current.style.background = "#ff6969";
                box_left.current.style.background = "#ff6969";
                return;
            }

            if (next_back_base_percentage > limitMax.current) {
                box.current.style.backgroundColor = '#ff6969';
            } else {
                box.current.style.backgroundColor = null;
            }

            let percentage = Math.max(0, Math.min(back_base_percentage, limitMax.current));

            let distance_value = linear(start.current, end.current, percentage);

            if (direction.current === 1) {
                distance_value = (Math.round((distance_value + Number.EPSILON) * 100) / 100)
                max.current = distance_value
                dr_value_right.current.textContent = `${distance_value.toFixed(2)} €`;
            } else {
                distance_value = (Math.round((distance_value + Number.EPSILON) * 100) / 100)
                min.current = distance_value
                dr_value_left.current.textContent = `${distance_value.toFixed(2)} €`;
            }

            box.current.parentElement.style.setProperty(
                directionSTR.current, `max(0px, ${percentage * 100}% - ${box_right.current.getBoundingClientRect().width}px)`
            );

            update_bar();
        }, [update_bar, delta_value, max_base, min_base]
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
        (event) => {
            cleanEvent()
            document.body.style.cursor = null;
            document.body.style.userSelect = null;
            box_right.current.style.backgroundColor = null;
            box_left.current.style.backgroundColor = null;

            if (min.current !== minFetch.current || max.current !== maxFetch.current) {
                minFetch.current = min.current
                maxFetch.current = max.current

                drChange({ 'min': minFetch.current, 'max': maxFetch.current })
            }
        }, [drChange, cleanEvent])

    const downCallback = useCallback(
        (event) => {
            cleanEvent()
            dirMouse.current = null
            tMinusOnePagex.current = null

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
        directionSTR.current = "left";
        start.current = min_base;
        end.current = max_base;
        box.current = box_left.current

        limitMax.current = reverse_linear(start.current, end.current, max.current - 2);
        downCallback(e)
    }, [downCallback, max_base, min_base])

    const rightDown = useCallback((e) => {
        direction.current = 1
        directionSTR.current = "right"
        start.current = max_base
        end.current = min_base;
        box.current = box_right.current

        limitMax.current = reverse_linear(start.current, end.current, min.current + 2);
        downCallback(e)
    }, [downCallback, min_base, max_base])

    return <nav className="range_filter">
        <ul>
            <li>
                <div ref={dr_value_left} className="dr_value_left text-left">
                    {min_base && min_base.toFixed(2)} €
                </div>
                <div ref={dr_main} className="dr_main">
                    <div className="dr_wrapper">
                        <div ref={box_left} onMouseDown={leftDown} className="dr_box"></div>
                    </div>
                    <div className="dr_wrapper">
                        <div ref={box_right} onMouseDown={rightDown} className="dr_box"></div>
                    </div>
                    <div ref={dr_witness} className="double_range_temoin">
                    </div>
                    <div ref={dr} className="double_range">
                    </div>
                </div>
                <div ref={dr_value_right} className="dr_value_right text-right">
                    {max_base && max_base.toFixed(2)} €
                </div>
            </li>
        </ul>
    </nav>
}

export default DoubleRange;
