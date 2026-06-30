import { THEME } from "@theme/index";
import React from "react";
import styled from "styled-components";
import { IoIosArrowBack } from "react-icons/io";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@components/form";
import { baseRequest } from "@request/request";
const Titles = styled.div`
  display: flex;
  align-items: center;
  /* max-width: ${(props) => (props.width ? props.width : "326px")}; */
  gap: 8px;
  /* background:red; */
  justify-content:space-between;
  .icon {
    display: flex;
    align-items: center;
    cursor: pointer;
    padding: 0px 10px;
  }
  .newTab{
    background:${THEME.primary};
    text-decoration:none;
    color:#fff;
    padding:8px 18px;
    border-radius:8px;
  }
  & span {
    display: inline-block;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    cursor: pointer;
    /* box-shadow:${THEME.button_box_shadow} */
  }
  & h2 {
    font-size: 24px;
    font-family: Rubik;
    color: ${THEME.primary_color_dark};
    font-weight: 500;
    background-color: #FFFFFF;
  }
`;
const TitleScroll = styled.div`
  & h2 {
    font-size: 1.1rem;
    color: ${THEME.primary};
    font-weight: 800;
  }
`;
const FormTitles = styled.div`
  /* margin: auto; */
  & h2 {
    font-size: 18px;
    color: #5B626B;
    font-weight: 600;
    text-transform: capitalize;
    margin-bottom: 10px;
  }
`;
const FormSubTitles = styled.div`
  & h4 {
    font-size: 14px;
    color: ${THEME.gray};
    font-weight: 500;
    text-transform: capitalize;
    border-bottom: 1px solid ${THEME.gray};
    margin: 10px;
  }
`;
export const CustomPageTitle = ({
  back,
  Heading,
  style,
  right,
  icon,
  width,
  newpage,
}) => {
  //  =======  GO Back To the pages
  const navigate = useNavigate();
  const locationName = useLocation();
  const PreviousPage = () => {
    navigate(-1);
  };
  return (
    <>
      <Titles width={width} style={style}>
        {/* <h2>{Heading}</h2>
        { newpage && <a className="newTab" href={locationName?.pathname} target="_blank">New Tab</a>} */}
        <a href={locationName?.pathname} target="_blank">
          <h2>{Heading}</h2>
        </a>
      </Titles>
      <hr
        style={{
          background: THEME.primary,
          width: "52px",
          height: "3px",
          marginBottom: "25px",
        }}
      ></hr>
    </>
  );
};
export const CustomPageTitleScroll = ({ Heading }) => {
  return (
    <TitleScroll>
      <h2>{Heading}</h2>
    </TitleScroll>
  );
};
export const CustomPageFormTitle = ({ Heading }) => {
  return (
    <FormTitles>
      <h2 style={{ color: "#FF4D00" }}> {Heading} </h2>
    </FormTitles>
  );
};
export const CustomPageFormTitle2 = ({ Heading }) => {
  return (
    <FormTitles>
      <h3 style={{ color: "#FF4D00" }}> {Heading} </h3>
    </FormTitles>
  );
};
export const CustomPageFormSubTitle = ({ Heading }) => {
  return (
    <FormSubTitles>
      <h4>{Heading}</h4>
    </FormSubTitles>
  );
};