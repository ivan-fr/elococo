import React, { useContext } from 'react';
import { doubleRangeContext } from '../contexts/double_range';


function DoubleRange() {
    const {min_base, max_base} = useContext(doubleRangeContext)

    return <nav className="range_filter">
        <ul>
            <li>
                <div className="dr_value_left text-left" data-dr-left={min_base}>
                    {min_base} €
                </div>
                <div className="dr_main">
                    <div className="dr_wrapper">
                        <div className="dr_box"></div>
                    </div>
                    <div className="dr_wrapper">
                        <div className="dr_box"></div>
                    </div>
                    <div className="double_range_temoin">
                    </div>
                    <div className="double_range">
                    </div>
                </div>
                <div className="dr_value_right text-right" data-dr-right={max_base}>
                    {max_base} €
                </div>
            </li>
        </ul>
    </nav>
}

export default DoubleRange;
