import React, { useEffect} from "react";
import { NavTopDraw } from "../Style";
import { RiMenu4Line } from 'react-icons/ri'
import { useDispatch, useSelector } from "react-redux";
import { Flex } from "@components/others";
import { selectCurrentUser } from "@modules/Auth/authSlice";
import { getManagement, selectManagementDetails } from "@modules/Management/ManagementSlice";

export const NavHeader = ({ showDrawer }) => {

  const dispatch = useDispatch();

  const AllManagementDetails = useSelector(selectManagementDetails);
  const nameDetails = useSelector(selectCurrentUser);

  useEffect(() => {
    dispatch(getManagement())
  }, [])

  return (
    <NavTopDraw>
      <Flex spacebetween={'true'} aligncenter={'true'} H_100={'true'}>
        <span className="DrawBtn" onClick={showDrawer} >
          <RiMenu4Line style={{ fontSize: "20px" }} />
        </span>
        <h3 style={{ color: '#065F46', fontFamily: '"Raleway", sans-serif', fontWeight: 700 }} className="ResponMobile">
          {AllManagementDetails?.temple_name}</h3>
        <p style={{ color: '#065F46', fontFamily: '"Raleway", sans-serif', fontSize: 25, fontWeight: 700 }}>
          {nameDetails}</p>
      </Flex>
    </NavTopDraw>
  );
};
