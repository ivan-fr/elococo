function dr(dr_grid, on_up) {
    let dr = dr_grid.querySelector(".dr_main .double_range");
    let dr_temoin = dr_grid.querySelector(".dr_main .double_range_temoin");
    let box_left = dr_grid.querySelector(".dr_main .dr_wrapper:nth-of-type(1) .dr_box");
    let box_right = dr_grid.querySelector(".dr_main .dr_wrapper:nth-of-type(2) .dr_box");
    let zIndex = 10;

    let dr_main = dr_grid.querySelector(".dr_main");

    let dr_value_left = dr_grid.querySelector(".dr_value_left");
    let dr_value_right = dr_grid.querySelector(".dr_value_right");

    let dr_value_left_init = parseFloat(dr_value_left.getAttribute("data-dr-left").replace(',', '.'));
    let dr_value_right_init = parseFloat(dr_value_right.getAttribute("data-dr-right").replace(',', '.'));

    let dr_chosen_value_left_init = dr_value_left.getAttribute("data-dr-left").replace(',', '.');
    let dr_chosen_value_right_init = dr_value_right.getAttribute("data-dr-right").replace(',', '.');

    let limit_quotient = {0: null, 1: null};
    let last_quotient = {0: null, 1: null};

    function linear(start, end, x) {
        let a = (end - start);
        return x * a + start;
    }

    function reverse_linear(start, end, r) {
        let a = (end - start);
        return (r - start) / a;
    }

    function callback_move(box, direction) {
        let init_page_x = null;
        let t_minus_one_page_x = null;
        let last_dir_mouse = null;
        let just_change = null;

        let limit_max;
        let limit_min = 0.;
        let direction_str;
        let start, end;

        if (direction === 1) {
            direction_str = "right";
            start = dr_value_right_init;
            end = dr_value_left_init;
            limit_max = Math.round(((dr_main.getBoundingClientRect().right - box_left.getBoundingClientRect().left) / dr_main.getBoundingClientRect().width + Number.EPSILON) * 100) / 100;
        } else {
            direction_str = "left";
            start = dr_value_left_init;
            end = dr_value_right_init;
            limit_max = Math.round(((box_right.getBoundingClientRect().right - dr_main.getBoundingClientRect().left) / dr_main.getBoundingClientRect().width + Number.EPSILON) * 100) / 100;
        }

        return function move(event) {
            if (event.type === "touchmove") {
                event.pageX = event.touches[0].pageX;
            }

            if (init_page_x === null) {
                init_page_x = event.pageX;
            }

            let dir_mouse;
            if (t_minus_one_page_x !== null) {
                if (event.pageX - t_minus_one_page_x > 0) {
                    dir_mouse = 0
                } else if (event.pageX - t_minus_one_page_x < 0) {
                    dir_mouse = 1
                } else {
                    dir_mouse = last_dir_mouse
                }
            } else {
                t_minus_one_page_x = event.pageX;
                return;
            }

            just_change = last_dir_mouse !== dir_mouse;

            last_dir_mouse = dir_mouse;
            t_minus_one_page_x = event.pageX;

            let delta_value = dr_value_right_init - dr_value_left_init
            let starter;
            if (direction === 1) {
                if (dir_mouse === 1) {
                    starter = dr_value_right_init;
                } else {
                    starter = dr_value_right_init - Math.floor(delta_value / 2) * 2;
                }
            } else {
                if (dir_mouse === 1) {
                    starter = dr_value_left_init + Math.floor(delta_value / 2) * 2;
                } else {
                    starter = dr_value_left_init;
                }
            }

            let base_percentage, function_quotient, function_quotient_2;
            if (direction === 1) {
                function_quotient = (dir_mouse === 1) ? Math.floor : Math.ceil;
                function_quotient_2 = (dir_mouse === 1) ? Math.floor : Math.ceil;
                base_percentage = Math.max(limit_min, Math.min((dr_main.getBoundingClientRect().right - event.pageX) / dr_main.getBoundingClientRect().width, limit_max));
            } else {
                function_quotient = (dir_mouse === 0) ? Math.floor : Math.ceil;
                function_quotient_2 = (dir_mouse === 0) ? Math.ceil : Math.floor;
                base_percentage = Math.max(limit_min, Math.min((event.pageX - dr_main.getBoundingClientRect().left) / dr_main.getBoundingClientRect().width, limit_max));
            }

            let start_bis, end_bis;
            if (direction !== dir_mouse) {
                [start_bis, end_bis] = [end, start]
            } else {
                [start_bis, end_bis] = [start, end]
            }

            let value = linear(start_bis, end_bis, base_percentage);
            let quotient_relative = Math.sign(function_quotient_2((value - starter) / 2)) * function_quotient(Math.abs(value - starter) / 2);

            if (direction !== dir_mouse) {
                quotient_relative *= -1;
            }

            let func;
            if (direction === 1) {
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
                if (direction === 1) {
                    sign = -1;
                } else {
                    sign = 1
                }
            }

            if (just_change === true) {
                limit_quotient[direction] = func(Math.abs(quotient_relative), Math.abs(last_quotient[direction])) * sign;
            }

            if (limit_quotient[direction] !== null) {
                quotient_relative = func(Math.abs(quotient_relative), Math.abs(limit_quotient[direction])) * sign;
            }

            last_quotient[direction] = quotient_relative;

            let value_target_end;

            if (direction === 1) {
                value_target_end = parseFloat(dr_value_left.getAttribute("data-dr-left").replace(',', '.')) + 2;
                limit_max = reverse_linear(start, end, value_target_end);
            } else {
                value_target_end = parseFloat(dr_value_right.getAttribute("data-dr-right").replace(',', '.')) - 2;
                limit_max = reverse_linear(start, end, value_target_end);
            }

            if (dir_mouse !== direction) {
                sign *= -1
            }

            let next_value_target = start + 2 * (quotient_relative + sign);
            let next_back_base_percentage = reverse_linear(start, end, next_value_target);
            let value_target = start + 2 * quotient_relative;
            let back_base_percentage = reverse_linear(start, end, value_target);

            if (isNaN(back_base_percentage)) {
                box_right.style.background = "#ff6969";
                box_left.style.background = "#ff6969";
                return;
            }

            console.log(next_back_base_percentage, dir_mouse, quotient_relative)

            if (next_back_base_percentage > limit_max || (next_back_base_percentage < limit_min && base_percentage)) {
                box.style.backgroundColor = '#ff6969';
            } else {
                box.style.backgroundColor = null;
            }

            let percentage = Math.max(limit_min, Math.min(back_base_percentage, limit_max));

            let distance_value = linear(start, end, percentage);

            if (direction === 1) {
                distance_value = (Math.round((distance_value + Number.EPSILON) * 100) / 100)
                dr_value_right.setAttribute("data-dr-right", `${distance_value}`);
                dr_value_right.textContent = `${distance_value.toFixed(2).toString().replace(".", ",")} €`;
            } else {
                distance_value = (Math.round((distance_value + Number.EPSILON) * 100) / 100)
                dr_value_left.setAttribute("data-dr-left", `${distance_value}`);
                dr_value_left.textContent = `${distance_value.toFixed(2).toString().replace(".", ",")} €`;
            }

            box.parentElement.style.setProperty(
                direction_str, `max(0px, ${percentage * 100}% - ${box_right.getBoundingClientRect().width}px)`
            );

            update_bar();
        };
    }

    function update_bar() {
        let px_2 = Math.abs((box_right.getBoundingClientRect().right - box_left.getBoundingClientRect().left - box_left.getBoundingClientRect().width));
        let px_3 = (box_left.getBoundingClientRect().left - dr_temoin.getBoundingClientRect().left + box_left.getBoundingClientRect().width);
        dr.style.width = `${px_2}px`;
        dr.style.left = `${px_3}px`;
    }

    window.addEventListener('resize', update_bar);

    function callback_up(move_callback, touch = 0) {
        return function up() {
            document.removeEventListener(get_name_event("move", touch), move_callback);
            document.body.style.cursor = null;
            document.body.style.userSelect = null;
            move_callback = null;
            box_right.style.backgroundColor = null;
            box_left.style.backgroundColor = null;

            let left = dr_value_left.getAttribute("data-dr-left").replace(",", ".");
            let right = dr_value_right.getAttribute("data-dr-right").replace(",", ".")

            if (left !== dr_chosen_value_left_init || right !== dr_chosen_value_right_init) {
                dr_chosen_value_right_init = right
                dr_chosen_value_left_init = left

                on_up(
                    dr_chosen_value_left_init,
                    dr_chosen_value_right_init
                );
            }

            document.removeEventListener("mouseup", up);
        }
    }

    function get_name_event(key, touch = 0) {
        let dico;
        if (touch) {
            dico = {"move": "mousemove", "up": "mouseup", "down": "mousedown"}
        } else {
            dico = {"move": "touchmove", "up": "touchend", "down": "touchstart"}
        }
        return dico[key];
    }

    function callback_down(direction, touch = 0) {
        return function down(event) {
            event.currentTarget.parentElement.style.zIndex = `${zIndex}`;
            zIndex++;
            let move_event = callback_move(event.currentTarget, direction);
            document.body.style.cursor = "move";
            document.body.style.userSelect = "none";
            document.addEventListener(get_name_event("move", touch), move_event);
            document.addEventListener(get_name_event("up", touch), callback_up(move_event, touch));
        }
    }

    box_left.addEventListener(get_name_event("down"), callback_down(0));

    box_right.addEventListener(get_name_event("down"), callback_down(1));

    box_left.addEventListener(get_name_event("down", 1), callback_down(0, 1));

    box_right.addEventListener(get_name_event("down", 1), callback_down(1, 1));
}