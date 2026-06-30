import React, { Fragment, useLayoutEffect } from "react";
import GlobalStyle from "@theme/GlobalStyle";
import { useLocation } from "react-router-dom";
import Routers from "./router";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./App.css";
import { selectCurrentToken } from "@modules/Auth/authSlice";
import { useSelector } from "react-redux";

function App() {
  const location = useLocation();
  const token = useSelector(selectCurrentToken);

  useLayoutEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  return (
    <Fragment>
      <GlobalStyle />
      <Routers token={token} />
      <ToastContainer />
    </Fragment>
  );
}

export default App;
