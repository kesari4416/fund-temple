import { createGlobalStyle } from 'styled-components'

const GlobalStyle = createGlobalStyle`
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
        -webkit-font-smoothing: antialiased;
    }

    h1, h2, h3, h4, .ant-page-title, .anticon-heading {
        font-family: 'Fraunces', 'Plus Jakarta Sans', serif;
        letter-spacing: -0.01em;
    }

    & .ant-menu-item-icon {
        font-size: 22px !important;
    }

    .ant-drawer .ant-drawer-body {
        padding: 0 !important;
        overflow: hidden !important;
    }

    .scroll {
        overflow-y: scroll;
    }

    ::-webkit-scrollbar {
        width: 0px;
        height: 10px;
    }
    ::-webkit-scrollbar-track {
        box-shadow: inset 0 0 5px rgba(6, 95, 70, 0.18);
        cursor: pointer;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(6, 95, 70, 0.45);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(6, 95, 70, 0.65);
        visibility: visible;
    }

    /* Form spacing */
    .ant-form-item {
        margin-bottom: 8px !important;
    }

    /* Main body bg (calmer cream-mint) */
    .ant-layout {
        background: #F4F8F5;
    }

    .ant-picker:hover {
        border-color: #065F46 !important;
    }

    .ant-input-affix-wrapper > input.ant-input {
        font-weight: 500 !important;
    }

    .ant-form label {
        border-radius: 50% !important;
    }

    /* Tabs */
    .ant-tabs .ant-tabs-tab.ant-tabs-tab-active .ant-tabs-tab-btn {
        color: #065F46 !important;
        box-shadow: 0 5px 10px 0 rgba(6, 95, 70, 0.15);
        border-radius: 0 0 6.585px 6.585px;
        text-decoration: none;
    }
    .ant-tabs .ant-tabs-tab-btn {
        padding: 10px;
    }
    .GHsZr .ant-tabs-tab {
        color: #252525;
        overflow: hidden;
    }

    /* === Table refresh: cleaner spacing, subtle dividers, branded header === */
    .ant-table {
        font-size: 14px;
    }
    .ant-table-thead > tr > th {
        background: #ECFDF5 !important;
        color: #064E3B !important;
        font-weight: 700 !important;
        font-size: 13px;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        border-bottom: 1px solid #D1FAE5 !important;
        padding: 14px 16px !important;
    }
    .ant-table-tbody > tr > td {
        padding: 12px 16px !important;
        color: #374151;
        border-bottom: 1px solid #F1F5F4 !important;
    }
    .ant-table-tbody > tr:hover > td {
        background: #F0FDF4 !important;
    }
    .ant-table-tbody > tr:nth-child(even) > td {
        background: #FAFBFA;
    }
    .ant-table-tbody > tr:nth-child(even):hover > td {
        background: #F0FDF4 !important;
    }
    .ant-pagination .ant-pagination-item-active {
        background: #065F46 !important;
        border-color: #065F46 !important;
    }
    .ant-pagination .ant-pagination-item-active a {
        color: #fff !important;
    }
    .ant-pagination .ant-pagination-item:hover {
        border-color: #065F46 !important;
    }
    .ant-pagination .ant-pagination-item:hover a {
        color: #065F46 !important;
    }

    /* Buttons: deeper shadow on hover */
    .ant-btn-primary {
        background: #065F46 !important;
        border-color: #065F46 !important;
        box-shadow: 0 4px 10px rgba(6, 95, 70, 0.18) !important;
    }
    .ant-btn-primary:hover, .ant-btn-primary:focus {
        background: #064E3B !important;
        border-color: #064E3B !important;
        box-shadow: 0 6px 14px rgba(6, 95, 70, 0.28) !important;
    }

    /* Tag presets */
    .ant-tag {
        border-radius: 6px;
        padding: 2px 10px;
        font-weight: 600;
    }

    /* Card subtle elevation */
    .ant-card {
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }

    /* Inputs subtle focus ring */
    .ant-input:focus, .ant-input-focused,
    .ant-input-affix-wrapper:focus, .ant-input-affix-wrapper-focused,
    .ant-select-focused .ant-select-selector,
    .ant-picker-focused {
        border-color: #065F46 !important;
        box-shadow: 0 0 0 3px rgba(6, 95, 70, 0.12) !important;
    }
`


export default GlobalStyle
