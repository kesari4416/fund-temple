import { THEME } from "@theme/index";
import { Layout, Menu } from "antd";
import styled from "styled-components";

export const MainLayout = styled.section`
  min-height: 100vh;
  display: flex;
  width: 100%;
  overflow: hidden;
  transition: 0.5s;
  /* overflow-y: hidden !important; */
`;
export const ImageProfile = styled.div`
  cursor: pointer;
  & img {
    width: 50px;
    margin: auto;
    border-radius: 50%;
  }
`;

export const MenuImageProfile = styled.div`
  width: 160px;
  height: 160px;
  background: red;
  position: relative;
  border-radius: 15px;
  overflow: hidden;
  margin-bottom: 20px;
  box-shadow: rgba(0, 0, 0, 0.15) 1.95px 1.95px 2.6px;
  transition: 0.3s;

  & img {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &.active {
    color: white !important;
    width: 50px;
    height: 50px;
  }
`;

export const MenuHolder = styled.div`
  /* height:calc(100vh - 380px);  // NO Img calc(100vh - 100px) */
  height: calc(100vh - 120px); // NO Img calc(100vh - 100px)
  overflow: auto;
`;

export const MenuBottom = styled.div`
  position: absolute;
  width: 100%;
  bottom: 0;
  display: flex;
  justify-content: center;
  padding: 13px 20px;
  background: ${THEME.primary};
  cursor: pointer;
  & svg {
    color: #000;
    font-size: 20px;
    margin-right: 10px;
  }
  & h1 {
    color: #fff;
  }
  :hover {
    opacity: 0.8;
  }
`;

export const LogoutBottom = styled.div`
  position: absolute;
  width: 100%;
  bottom: 0;
  display: flex;
  justify-content: center;
  padding: 13px 20px;
  color: #000;
  background: ${THEME.primary};
  
`;

export const Profile = styled.div`
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 20px 0 10px 0px;
  gap: 10px;
  padding: 5px 20px;
`;

export const MenuText = styled.div`
  font-size: 16px;
  color: #545454;
  padding-left: 7px;
  margin-top: 10px;
`;

export const HeaderNav = styled.div`
  display: flex;
  align-items: center;
  padding: 13px 21px;
  z-index: 999;
  background: #ffffff;

  & span {
    padding: 2px;
    cursor: pointer;

    :hover {
      & svg {
        fill: #fff;
      }
    }
  }

  & h3 {
    padding-left: 10px;
    font-size: 20px;
    margin-left: 10px;
    color: #990000;
    font-weight: 800;
    visibility: visible;
    opacity: 1;
    width: 100%;
    transition: 0.3s;

    &.active {
      color: white !important;
      width: 0px;
      visibility: hidden;
      opacity: 0;
      transition: 0.3s;
    }
  }

& p {
  font-size: 10px;

}
`;

export const NavTopDraw = styled.div`
  height: inherit;

  .ant-btn {
    border-radius: 0px !important;
  }

  .notify {
    cursor: pointer;
  }
  .ResponMobile {
    font-size: 1.5vw;
    letter-spacing: 1px;
    word-spacing: 5px;
  }

  @media screen and (max-width: 800px) {
    .ResponMobile {
      font-size: 2vw;
    }
  }

  @media screen and (max-width: 431px) {
    .ResponMobile {
      /* font-size: 1vw; */
      display: 'none';
    }
  }



  @media (min-width: 901px) {
    .DrawBtn {
      display: none;
    }
  
    .Btnresponsive {
      width: 30%;
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 15px !important;
    }
  }

  @media (max-width: 901px) {
    .DrawBtn {
      cursor: pointer;
      padding: 5px;
    }
    p{
      display: none;
    }

    .Btnresponsive {
      display: flex;
      align-items: center;
      gap: 15px !important;
    }
  }

  &.btnborder .icon {
    font-size: 3px;
    margin-right: 10px;
  }
`;

export const SideMenuLayout = styled(Layout.Sider)`
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;

  @media (max-width: 900px) {
    display: none;
  }

  .ant-btn-text:not(:disabled):not(.ant-btn-disabled):hover {
    background-color: ${THEME.primary};
  }
  .ant-btn-text:not(:disabled):not(.ant-btn-disabled):hover .anticon svg {
    color: ${THEME.black} !important;
  }
  .ant-btn {
    border-radius: 0px !important;
  }
  .anticon svg {
    font-size: 18px;
    color: ${THEME.primary} !important;
  }
  .anticon svg:hover {
    color: ${THEME.black} !important;
  }
  .ant-layout .ant-layout-sider-children {
    background: #fff !important;
  }
  .ant-layout-sider-children {
    /* background: red !important; */
    background: #fff;

    /* 0 0 4px 4px rgba(0, 0, 0, 0.08) */
    border-right: 1px solid #e8e8e8;
  }
  .ant-menu-dark {
    background: #ffffff !important;
  }

  .ant-menu-light:not(.ant-menu-horizontal)
    .ant-menu-item:not(.ant-menu-item-selected):active {
    color: white !important;
    background-color: #990000 !important;
    border-radius: 10px !important;
  }

  .ant-menu-light {
    /* background: #000 !important; */

    // background: linear-gradient(0deg, rgb(239 127 26 / 0%) 0%, rgb(243 188 46 / 0%) 29%, rgba(0, 2, 5, 0.992) 87%);
    // color: #fff;
  }
  .ant-menu-light .ant-menu-item-selected {
    background-color: ${THEME.primary};
    color: ${THEME.secondary};
    border-radius: 10px solid;
  }
  /* .ant-menu-light .ant-menu-item-selected {} */

  .ant-menu .ant-menu-item {
    /* border-radius: 15% !important; */

    /* border-right: 1px solid; */
  }
  .ant-menu-light .ant-menu-submenu-selected > .ant-menu-submenu-title {
    color: ${THEME.primary};
  }

  .ant-menu-light .ant-menu-item-selected {
    border-right: 2px solid !important;
    border-radius: 15px;
    margin-left: -21px;
  }

  .ant-menu-light
    .ant-menu-item:not(.ant-menu-item-selected):not(
      .ant-menu-submenu-selected
    ):hover {
    color: ${THEME.primary} !important;
  }
  .ant-menu-light:not(.ant-menu-horizontal)
    .ant-menu-item:not(.ant-menu-item-selected):hover {
    background-color: transparent !important;
  }
  .ant-menu-light:not(.ant-menu-horizontal) .ant-menu-submenu-title:hover {
    background-color: transparent !important;
  }
  .ant-menu-light.ant-menu-inline .ant-menu-sub.ant-menu-inline {
    background-color: transparent !important;
  }
  .ant-menu-item .ant-menu-item-icon + span {
    margin-inline-start: 20px !important;
  }
  .ant-menu .ant-menu-submenu-title .ant-menu-item-icon + span {
    margin-inline-start: 20px !important;
  }
`;

export const TopHeader = styled(Layout.Header)`
  /* @media screen and (min-width: 901px) {
    display: none;
} */

  height: 70px !important;
  box-shadow: 0 0 4px 4px rgba(0, 0, 0, 0.08) !important;
  background: ${THEME.white};
  line-height: 0;
`;

export const BodyContent = styled(Layout.Content)`
  height: 80vh;
  overflow-y: auto;
  & .ant-menu-item-icon {
    font-size: 20px !important;
  }
  & .ant-menu .ant-menu-item .ant-menu-item-icon {
    font-size: 20px !important;
  }

  @media (max-width: 900px) {
    & .ant-layout-content {
      width: 100% !important;
      margin: 0 !important;
    }
  }
`;

export const AntdStyledMenu = styled(Menu)`
  position: absolute !important;
  right: 3px;
  box-shadow: rgba(0, 0, 0, 0.2) 0px 5px 5px -3px,
    rgba(0, 0, 0, 0.14) 0px 8px 10px 1px, rgba(0, 0, 0, 0.12) 0px 3px 14px 2px !important;
  .ant-dropdown-menu-item {
    padding: 10px 12px !important;
    color: "#757575" !important;
  }
  .ant-dropdown-menu-item-icon {
    margin-inline-end: 16px !important;
  }
`;

export const BtnProfile = styled.div`
  margin: 0 10px;
  padding: 9px;
  display: flex;
  color: black !important;
  border-radius: 25px;
  cursor: pointer;
  align-items: center;
  justify-content: flex-end;
  padding-right: 20px;

  

  & h1 {
    display: flex;
    justify-content: flex-start;
    font-weight: 600;
    padding-right: 9px;
  }

  & svg {
    font-size: 1.5rem;
    color: "#111827";
  }

  &:hover {
    background: #d9d9e75e;
  }

  & .header__icon {
    font-size: 26px;
    color: "white";
  }

  .sc-kTbCBX.fwiJiO {
    background-color: #ffffff;
  }
`;
