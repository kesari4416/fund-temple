import React from "react";
import FirstLogo from "../../../assets/images/amman.jpg";
import { CustomCardView } from "@components/others";
import { useSelector } from "react-redux";
import { selectManagementDetails } from "@modules/Management/ManagementSlice";
import { useNavigate } from "react-router-dom";

const HomeView = () => {

  const navigate = useNavigate();
  const ManagementDetails = useSelector(selectManagementDetails);

  return (
    <CustomCardView>
      {/* {ManagementDetails && ManagementDetails?.images ? (
        <img
          src={ManagementDetails.images}
          style={{ width: "100%", height: "auto", objectFit: 'cover' }}
        />
      ) : ( */}
        <img src={FirstLogo} style={{ width: "100%", height: "auto", objectFit: 'cover' }} />
      {/* )} */}
    </CustomCardView>
  );
};

export default HomeView;
