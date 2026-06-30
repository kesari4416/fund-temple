import { createGlobalStyle } from 'styled-components'

const GlobalStyle = createGlobalStyle`
    * {
        margin:0;
        padding: 0;
        box-sizing:border-box;
        font-family: 'Rubik';
    }

  & .ant-menu-item-icon {
    font-size: 23px !important;
   }

   .ant-drawer .ant-drawer-body {
    padding: 0% !important;
    overflow: hidden !important;
   }

   .scroll {
    overflow-y: scroll;
   }

   ::-webkit-scrollbar {
    width: 0px;
    height: 10px;
    }

    /* Track */
    ::-webkit-scrollbar-track {
        box-shadow: inset 0 0 5px #1677ff;
        cursor: pointer;
        border-radius: 10px;

    }

    /* Handle */
    ::-webkit-scrollbar-thumb {
        background: rgb(3 108 255 / 43%);
        border-radius: 10px;
    }

    /* Handle on hover */
    ::-webkit-scrollbar-thumb:hover {
        background: rgb(3 108 255 / 43%);
        visibility: visible;
    }

    /* Antd Form  */
    .ant-form-item {
        margin-bottom: 6px !important;
    }

    /* Main body bg color  */
    .ant-layout {
        background: #FFF5F5;
    }

    .ant-picker:hover {
        border-color: #d9d9d9 !important;
    }

    .ant-input-affix-wrapper >input.ant-input {
        font-weight: 500 !important;
    }
    .ant-form label {
    /* padding: 0 10px !important; */
    border-radius: 50% !important;
    }

.ant-tabs .ant-tabs-tab.ant-tabs-tab-active .ant-tabs-tab-btn {
   color :#252525 !important    ;
   box-shadow: 0px 5px 10px 0px rgba(155, 0, 0, 0.15);
   border-radius: 0px 0px 6.585px 6.585px;
   text-decoration: none;
}
.ant-tabs .ant-tabs-tab-btn{
    padding: 10px;
}

.GHsZr .ant-tabs-tab {
    color: #252525;
    overflow: hidden;
}
`


export default GlobalStyle
