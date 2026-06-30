const ROOT = {

    // =====  PRIMARY COLORS  ===========
    // Refreshed palette (Jun-2026): deep emerald + warm saffron gold,
    // calming, distinctive, temple-appropriate (replaces previous red/maroon).
    primary: '#065F46',
    primary_color_dark: '#064E3B',
    primary_color_light: '#0F766E',
    primary_color_gray1: '#1F2A37',
    primary_color_gray2: '#6B7280',

    secondary: '#ffffff',
    secondary_color_dark: '#B45309',
    secondary_color_light: '#D97706',


    // ======  Color  ======
    blue: '#96ADFF',
    indigo: '#6610f2',
    purple: '#6f42c1',
    pink: '#e83e8c',
    red: '#FF8787',
    black: '#000000',
    orange: '#fd7e14',
    yellow: '#ffc107',
    green: '#28a745',
    teal: '#20c997',
    cyan: '#17a2b8',
    white: '#fff',
    gray: '#6c757d',
    gray_dark: '#343a40',
    success: '#28a745',
    info: '#17a2b8',
    warning: '#ffc107',
    danger: '#dc3545',
    light: '#f8f9fa',
    dark_gold: '#D4A017',
    dark: '#343a40',
    danger_2: '#fff',
    primary_2: '#0F766E',
    table_head: '#1F2937',
    table_content: '#374151',
    table_nthchild: '#F4F8F5',

    // ======  SIZES  ======

    gutter_x: '1.5rem',
    gutter_y: '0',
    BTN_PRIMART: '#065F46',
    BTN_PRIMART_HOVER: '#064E3B',
    BTN_SECONDARY: '#B8860B',
    BTN_SECONDARY_HOVER: '#8C6508',
    TRANSPARENT: '#00000000',
    TRANSPARENT_HOVER: 'rgba(17, 24, 39, 0.04)',


    // =========  linear Gradient ======
    linear_gradiant1: 'linear-gradient(90deg, #065F46 2%, #0F766E 91%)',
    linear_gradiant2: 'linear-gradient(90deg, #B8860B 0%, #D4A017 100%)',
    // =========  Box Shadow ======
    button_box_shadow: 'rgba(6, 95, 70, 0.18) 0 4px 10px;',
    buttonHover_box_shadow: 'rgba(6, 95, 70, 0.24) 0 6px 14px;',

    form_box_shadow: 'rgba(15, 23, 42, 0.08) 0 4px 14px;',
    formHover_box_shadow: 'rgba(15, 23, 42, 0.14) 0 10px 28px, rgba(15, 23, 42, 0.06) 0 0 0 1px;'
}

// =======  Media Queries Start  ========

// ===========  Define breakpoints  ===========

const SIZES = {
    // mobileS: '320px',
    MOBILEM: '375px',
    MOBILEL: '576px',
    TABLET: '768px',
    LAPTOP: '992px',
    LAPTOPL: '1200px',
    DESKTOP: '1400px',
    DESKTOPL: '1800px',
}

// ===========  Define DEVICES  ===========

const DEVICES = {
    MOBILEM: `(min-width: ${SIZES.MOBILEM})`,
    MOBILEL: `(min-width: ${SIZES.MOBILEL})`,
    TABLET: `(min-width: ${SIZES.TABLET})`,
    LAPTOP: `(min-width: ${SIZES.LAPTOP})`,
    LAPTOPL: `(min-width: ${SIZES.LAPTOPL})`,
    DESKTOP: `(min-width: ${SIZES.DESKTOP})`,
    DESKTOPL: `(min-width: ${SIZES.DESKTOPL})`,
}

const ANTD_COLORS = {
    PRIMARY: '#065F46', // primary color for all components
    LINK: '#0F766E', // link color
    SUCCESS: '#16a34a', // success state color
    WARNING: '#D4A017', // warning state color
    ERROR: '#dc2626', // error state color
    GEEK_BLUE: 'gold', // tag colour family
    HEADING: '#0F172A', // heading text color
    TEXT_PRIMARY: '#111827', // major text color
    TEXT_SECONDARY: '#4B5563', // secondary text color
    DISABLED: 'rgba(0, 0, 0, .25)', // disable state color
    BORDER: '#E5E7EB', // major border color
}

const GREY_COLORS = {
    GREY_S_70: '#0F172A',
    GREY_S_50: '#1F2937',
    GREY_S_30: '#374151',
    GREY_S_20: '#4B5563',
    GREY_S_10: '#6B7280',
    GREY_100: '#6B7280',
    GREY_T_15: '#6B7280',
    GREY_T_25: '#9CA3AF',
    GREY_T_35: '#9CA3AF',
    GREY_T_50: '#D1D5DB',
    GREY_T_65: '#E5E7EB',
    GREY_T_75: '#E5E7EB',
    GREY_T_85: '#F3F4F6',
    GREY_T_92: '#F8FAF9',
    GREY_T_96: '#F9FAFB',
    GREY_T_98: '#FBFCFC',
    GREY_PALE: '#6B7280',
}

const GREEN_COLOR = {
    GREEN_PRIMARY: '#16a34a',
    GREEN_DARK: '#15803d',
    GREEN_LIGHT: '#22c55e',
    GREEN_T_15: '#22c55e',
    GREEN_T_50: '#86efac',
    GREEN_T_96: '#F0FDF4',
    GREEN_T_75: '#BBF7D0',
    GREEN_T_85: '#15803d',
    GREEN_S_56: '#16a34a',
    GREEN_100: '#16a34a',
    GREEN_PALE: '#22c55e'
}

const BLUE_COLORS = {
    BLUE_S_10: '#0F766E',
    BLUE_S_37: '#0F766E',
    BLUE_T_15: '#14B8A6',
    BLUE_T_25: '#14B8A6',
    BLUE_T_50: '#5EEAD4',
    BLUE_T_65: '#99F6E4',
    BLUE_T_69: '#5EEAD4',
    BLUE_T_92: '#ECFEFF',
    BLUE_S_30: '#065F46',
    BLUE_100: '#0F766E',
    BLUE_T_96: '#F0FDFA',
    BLUE_T_75: '#99F6E4',
    BLUE_T_85: '#CCFBF1',
}

const RED_COLORS = {
    RED_T_15: '#dc2626',
    RED_T_25: '#ef4444',
    RED_T_96: '#FEF2F2',
    RED_T_75: '#FECACA',
    RED_T_85: '#FEE2E2',
    RED_S_49: '#b91c1c',
    RED_S_50: '#991b1b',
    RED_S_100: '#dc2626',
    RED_100: '#dc2626',
}

const ORANGE_COLORS = {

    YELLOW_OR_80: '#D4A017',
    YELLOW_T_85: '#FEF3C7',
    YELLOW_OR_50: '#F59E0B',
    YELLOW_T_96: '#FFFBEB',
    YELLOW_T_35: '#FDE68A',
    YELLOW_T_75: '#FEF3C7',
    YELLOW_T_92: '#FFFBEB',
    YELLOW_T_50: '#FCD34D',
}

const PURPLE_COLORS = {
    PRIMARY_PURPLE: '#0F766E',
    PURPLE_T_80: '#0F766E',
    PURPLE_T_96: '#F0FDFA',
    PURPLE_T_75: '#99F6E4',
    PURPLE_100: '#0F766E',
    PURPLE_T_85: '#CCFBF1',
}


/**
 * CONFIGURE THEME HERE
 * **/
export const THEME = {
    ...ANTD_COLORS,
    ...GREY_COLORS,
    ...GREEN_COLOR,
    ...BLUE_COLORS,
    ...RED_COLORS,
    ...ORANGE_COLORS,
    ...PURPLE_COLORS,
    ...ROOT,
    ...DEVICES,
}
