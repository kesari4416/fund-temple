import React, { useEffect } from "react";
import { NavTopDraw } from "../Style";
import { RiMenu4Line } from "react-icons/ri";
import { useDispatch, useSelector } from "react-redux";
import { Flex } from "@components/others";
import { selectCurrentUser } from "@modules/Auth/authSlice";
import {
  getManagement,
  selectManagementDetails,
} from "@modules/Management/ManagementSlice";

export const NavHeader = ({ showDrawer }) => {
  const dispatch = useDispatch();

  const AllManagementDetails = useSelector(selectManagementDetails);
  const nameDetails = useSelector(selectCurrentUser);

  useEffect(() => {
    dispatch(getManagement());
  }, []);

  return (
    <NavTopDraw>
      <Flex
        spacebetween={"true"}
        aligncenter={"true"}
        H_100={"true"}
        style={{ width: "100%", gap: 12, paddingRight: 8 }}
      >
        <span className="DrawBtn" onClick={showDrawer}>
          <RiMenu4Line style={{ fontSize: "20px" }} />
        </span>
        <h3
          style={{
            color: "#990000",
            fontFamily: '"Raleway", sans-serif',
            fontWeight: 700,
            margin: 0,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            flex: 1,
            minWidth: 0,
          }}
          className="ResponMobile"
          title={AllManagementDetails?.temple_name}
        >
          {AllManagementDetails?.temple_name}
        </h3>
        <p
          style={{
            color: "#990000",
            fontFamily: '"Raleway", sans-serif',
            fontSize: 20,
            fontWeight: 700,
            margin: 0,
            whiteSpace: "nowrap",
            flexShrink: 0,
          }}
        >
          {nameDetails}
        </p>
      </Flex>
    </NavTopDraw>
  );
};
