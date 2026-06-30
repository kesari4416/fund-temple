import React, { Fragment } from "react";
import styled from "styled-components";
import { Button, Col, Form, Input, Spin } from "antd";
import { CustomRow, Flex } from "@components/others";
import { CustomInput, CustomInputPassword } from "@components/form";
import { SvgIcons } from "@assets/Svg";
import { LoadingOutlined } from "@ant-design/icons";

const FragmentStyle = styled.div`
  & svg {
    color: black;
  }
`;
const StyledLogo = styled.div`
  color: #900;
`;
const StyledButton = styled(Button)`
  display: flex;
  width: 95%;
  border-radius: 5px;
  background: #900;
  box-shadow: 4px 4px 20px 0px rgba(153, 0, 0, 0.25);
  align-items: center;
  text-align: center;
  justify-content: center;
  padding: 20px !important;
  margin-top: 30px;

  & p {
    color: white;
    :hover{
       background: #900;
    }
  }
`;
const SignInForm = ({ handleSignIn, isLoading }) => {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    handleSignIn(values);
    // form.resetFields();
  };

  return (
    <FragmentStyle>
      <Form
        onFinish={onFinish}
        labelCol={{
          span: 24,
        }}
        autoComplete="off"
        wrapperCol={{
          span: 24,
        }}
        form={form}
      >
        <CustomRow space={[24, 24]}>
          <Col span={24} md={24}>
            <Flex center={"true"}>
              <img src={SvgIcons.Logoimg} />
              <StyledLogo>
                <h1>Temple</h1>
              </StyledLogo>
            </Flex>
          </Col>
          <Col span={24} md={24}>
            <Flex center={"true"}>
              <h2>Sign In</h2>
            </Flex>
          </Col>
          <Col span={24}>
            <CustomInput
              name="email"
              type={"email"}
              label={"Email"}
              rules={[
                {
                  required: true,
                  message: "Required !",
                },
              ]}
            />
          </Col>

          <Col span={24}>
            <CustomInputPassword
              name="password"
              label={"Password"}
              rules={[
                {
                  required: true,
                  message: "Required !",
                },
              ]}
            />
          </Col>
        </CustomRow>
        <Flex center={"true"} gap={"20px"} margin={"20px 0"}>
          {isLoading ? (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: "30px",
                width: "60px",
                marginTop: "3px",
              }}
            >
              <Spin
                indicator={
                  <LoadingOutlined
                    style={{
                      fontSize: 20,
                    }}
                    spin
                  />
                }
              />
            </div>
          ) : (
            <StyledButton htmlType="submit">
              <p>Sign In</p>
            </StyledButton>
          )}
        </Flex>
      </Form>
    </FragmentStyle>
  );
};

export default SignInForm;
