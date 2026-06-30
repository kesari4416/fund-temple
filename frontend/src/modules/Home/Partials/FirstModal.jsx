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
      <div
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#fff",
        }}
      >
        <img
          src={FirstLogo}
          alt="Temple"
          style={{
            maxWidth: "100%",
            maxHeight: "calc(100vh - 180px)",
            width: "auto",
            height: "auto",
            objectFit: "contain",
            borderRadius: 8,
          }}
        />
      </div>
    </CustomCardView>
  );
};

export default HomeView;
