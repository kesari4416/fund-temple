import React, { Fragment, useEffect, useMemo, useState } from 'react'
import { CustomCardView, CustomModal, CustomRow, Flex } from '@components/others';
import { CustomPageTitle } from '@components/others/CustomPageTitle';
import { Card, Col, Collapse, Form, Tooltip } from 'antd';
import { StyledHeading } from '../style';
import styled from 'styled-components';
import request from '@request/request';
import { APIURLS } from '@request/apiUrls/urls';
import errorHandler from '@request/errorHandler';
import { Button } from '@components/form';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { AllChitList, getChitFundList } from '@modules/ChitFund/ChitFundSlice';
import { BondPaper } from './BondPaper';
import { IoIosPaper } from 'react-icons/io';

const Totalstyle = styled.div`
 & h3 {
        font-size:15px;
        color:#414040;
       
    }
    .ImgTotal {
        width: 150px;
        height: 150px;
        object-fit: cover;
        margin-bottom: 20px;
        overflow: hidden;
        & img {
            width: 100%;
            height: 100%;
            object-fit: scale-down;
        }
    } 
    .info-row {
    display: flex;
    align-items: flex-start;
    margin-bottom: 10px; 
}
.info-label {
    width: 200px; 
    font-weight: bold;
    color: #333; 
}
.info-value {
    flex: 1; 
}
.centerLabel {
    display: inline-block;
    width: 20px; 
    text-align: center;
}
`
;
const CardFooterStyle = styled(Card)`
margin:30px 0px;
width:100%;
.info-label-footer{
    font-size:17px;
    margin:20px 0px;
    font-weight: bold;
}   
`
;
const ChitFundListView = () => {

    const [form] = Form.useForm();
    const { id } = useParams();
    const dispatch = useDispatch();

    const [menberDetalView, setMenberDetalView] = useState({});
    const [findIds, setFindIds] = useState({});

    // Demand Share Amount = (Management Invested Amount + Outer Invest Amount + Profit Amount) / Investers Share Count
    // The "Investers Share Count" shown in the view already includes the management share, so this
    // divisor lines up with what the user sees.
    const demandShareAmount = useMemo(() => {
        const mgmtInvested = Number(findIds?.management_amt || 0);
        const outerInvest = Number(findIds?.outer_invest_amount || 0);
        const profitAmount = Number(findIds?.profit_amount || 0);
        const investerShares = Number(findIds?.investers_share_count || 0);
        if (!investerShares) return 0;
        const value = (mgmtInvested + outerInvest + profitAmount) / investerShares;
        return Number.isFinite(value) ? Number(value.toFixed(2)) : 0;
    }, [
        findIds?.management_amt,
        findIds?.outer_invest_amount,
        findIds?.profit_amount,
        findIds?.investers_share_count,
    ]);

    // Displayed "Investers Share Count" = actual investers + management share (as per user requirement).
    const investersShareCountDisplay = useMemo(() => {
        const investers = Number(findIds?.investers_share_count || 0);
        const mgmt = Number(findIds?.management_share_count || 0);
        return investers + mgmt;
    }, [findIds?.investers_share_count, findIds?.management_share_count]);

    const [isModalOpen, setIsModalOpen] = useState(false);
    // ======  Modal Title and Content ========
    const [modalTitle, setModalTitle] = useState("");
    const [modalContent, setModalContent] = useState(null);

    // ----------  Form Reset UseState ---------
    const [modelwith, setModelwith] = useState(0);

    // ===== Modal Functions Start =====
    const showModal = () => {
        setIsModalOpen(true);
    };

    const handleOk = () => {
        setIsModalOpen(false);
        ResetTrigger();
    };

    const handleCancel = () => {
        setIsModalOpen(false);
    };

    useEffect(() => {
        GetMemberDetails()
    }, [])


    const GetMemberDetails = async (data) => {
        await request.get(`${APIURLS.GET_MEMBER_CHITFUND_VIEW}/${id}/`, data)
            .then(function (response) {
                setMenberDetalView(response.data)
                return response.data;
            })
            .catch(function (error) {
                return errorHandler(error);
            })
    }

    const MemDetails = menberDetalView?.chitt_fund
    useEffect(() => {
        dispatch(getChitFundList())
    }, []);

    const AllDetails = useSelector(AllChitList);
    useEffect(() => {
        const FindId = AllDetails?.find((ids) => ids?.id == id)
        setFindIds(FindId)
    }, [AllDetails]);

    const handlebondClick = (values) => {
        setModelwith(900)
        setModalContent(<BondPaper InvestorRecord={values} AllChitDetails={findIds} findIds={findIds} />);
        showModal();
    }
    return (
        <Form
            name='ViewMemberProfile'
            form={form}
            labelCol={{
                span: 24,
            }}
            wrapperCol={{
                span: 24,
            }}
            autoComplete="off"
        >
            <CustomCardView>
                <CustomRow space={[12, 12]}>
                    <Col span={24} md={24}>
                        <CustomPageTitle Heading={'View Details'} />
                    </Col>
                    <Col span={24} md={12}>
                        <Totalstyle>
                            <div className="info-row">
                                <h3 className="info-label">Chit No </h3>
                                <span >:</span>&nbsp;&nbsp;
                                <span>{findIds?.chit_no}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Chit Name </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.chit_name}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Management Invested Amount </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.management_amt}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Management Share Count </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.management_share_count}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Management Retake Amount</h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.management_retake}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Retake mangement Share Count </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.retake_management_share_count}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Management Profit Precent </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.set_profit_percent}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Profit Amount </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.profit_amount}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Principal Given Amount </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.principal_given_amount}</span>
                            </div>
                        </Totalstyle>
                    </Col>
                    <Col span={24} md={12}>
                        <Totalstyle>
                            <div className="info-row">
                                <h3 className="info-label">Starting Date </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.starting_date}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Fixed Share Amount </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.fixed_chitfund_amount}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Outer Invest Amount </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.outer_invest_amount}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Investers Share Count </h3>
                                <span>:</span>&nbsp;
                                <span data-testid="investers-share-count-value">{investersShareCountDisplay}</span>
                            </div>
                            <div className="info-row" data-testid="demand-share-amount-row">
                                <h3 className="info-label">Demand Share Amount </h3>
                                <span>:</span>&nbsp;
                                <span data-testid="demand-share-amount-value">{demandShareAmount}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Invest Retake Amount </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.invest_retake}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Retake Invester Share Amount</h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.retake_investers_share_count}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Interest Precent</h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.set_intrest_percent}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Profit Retake </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.profit_retake}</span>
                            </div>
                            <div className="info-row">
                                <h3 className="info-label">Collected Principal Amount </h3>
                                <span>:</span>&nbsp;
                                <span>{findIds?.collected_principal_amount}</span>
                            </div>
                            <CardFooterStyle>
                                <h3 className="info-label-footer">Cash In Hand Amount&nbsp; :&nbsp;&nbsp;<span style={{color:'green'}}>₹&nbsp;{findIds?.cash_inhand_amount}</span> </h3>
                            </CardFooterStyle>
                        </Totalstyle>
                    </Col>

                    <Col span={24} md={18}>
                        <StyledHeading style={{ marginTop: "25px", textAlign: "left" }}>
                            <h2>Member  Details</h2>
                        </StyledHeading>
                    </Col>
                    <Col span={24} md={24}>
                        {MemDetails?.map((find, index) => (
                            <div style={{ padding: '20px', border: '2px solid', margin: '10px' }}>
                                <Flex spacebetween={true} aligncenter={true}>
                                    <h2 style={{ textDecoration: 'underline' }}>Member {index + 1}</h2>
                                    <Tooltip placement="top" title='Bond Paper'>
                                        <Flex end={true}><Button.Secondary onClick={() => handlebondClick(find)} icon={<IoIosPaper />} text={'Bond'} /> </Flex>
                                    </Tooltip>
                                </Flex>

                                <CustomRow>
                                    <Col span={24} md={12}>
                                        <Totalstyle>
                                            <div className="info-row">
                                                <h3 className="info-label">Name </h3>
                                                <span>:</span>&nbsp;
                                                <span>{find?.invester_name}</span>
                                            </div>
                                            <div className="info-row">
                                                <h3 className="info-label">Joining Date </h3>
                                                <span>:</span>&nbsp;
                                                <span>{find?.joining_date}</span>
                                            </div>
                                            <div className="info-row">
                                                <h3 className="info-label">Email ID  </h3>
                                                <span>:</span>&nbsp;
                                                <div className="info-value">{find?.invester_email}</div>
                                            </div>
                                            <div className="info-row">
                                                <h3 className="info-label">Mobile  </h3>
                                                <span>:</span>&nbsp;
                                                <span>{find?.invester_mobile}</span>
                                            </div>
                                            <div className="info-row">
                                                <h3 className="info-label">Address</h3>
                                                <span>:</span>&nbsp;
                                                <div className="info-value">{find?.invester_address}</div>
                                            </div>


                                            <div className="info-row">
                                                <h3 className="info-label">Invested Amt  </h3>
                                                <span>:</span>&nbsp;
                                                <span>{find?.investment_amt}</span>
                                            </div>
                                            <div className="info-row">
                                                <h3 className="info-label">Share Count  </h3>
                                                <span>:</span>&nbsp;
                                                <span>{find?.share_count}</span>
                                            </div>

                                            <div className="info-row">
                                                <h3 className="info-label">Share Amount  </h3>
                                                <span>:</span>&nbsp;
                                                <span>
                                                  {(() => {
                                                    // If the investor is already settled
                                                    // (application submitted -> action=false or
                                                    // application_date is set), show the FROZEN
                                                    // share_amount that was locked at settlement.
                                                    // Otherwise show the LIVE collected_share_amount.
                                                    const settled =
                                                      find?.action === false ||
                                                      !!find?.application_date;
                                                    const value = settled
                                                      ? find?.share_amount ?? 0
                                                      : find?.collected_share_amount ??
                                                        find?.share_amount ??
                                                        0;
                                                    return Number(value).toFixed(2);
                                                  })()}
                                                </span>
                                            </div>

                                            {Number(find?.final_settlement_amount || 0) > 0 && (
                                                <div className="info-row">
                                                    <h3 className="info-label">Final Settlement Amount  </h3>
                                                    <span>:</span>&nbsp;
                                                    <span style={{ color: '#0F5132', fontWeight: 600 }}>
                                                      ₹ {Number(find?.final_settlement_amount).toFixed(2)}
                                                    </span>
                                                </div>
                                            )}

                                            <div className="info-row">
                                                <h3 className="info-label">Retake Share Count  </h3>
                                                <span>:</span>&nbsp;
                                                <span>{find?.retake_share_count}</span>
                                            </div>

                                            <div className="info-row">
                                                <h3 className="info-label">Application Date </h3>
                                                <span>:</span>&nbsp;
                                                <span>{find?.application_date}</span>
                                            </div>
                                            <div className="info-row">
                                                <h3 className="info-label">Settlement Date  </h3>
                                                <span>:</span>&nbsp;
                                                <span>{find?.settlement_date}</span>
                                            </div>
                                        </Totalstyle>
                                    </Col>
                                    <Col span={24} md={12} key={find.id}>
                                        <Totalstyle style={{ float: 'right' }}>
                                            <div className='ImgTotal'>
                                                {find?.images ? (
                                                    <img src={find.images} alt='img' />
                                                ) : (
                                                    <span></span>
                                                )}
                                            </div>

                                        </Totalstyle>
                                    </Col>
                                    {find?.documents &&
                                        <Col span={24} md={24} style={{ margin: '10px 0px' }}>
                                            <Collapse
                                                size="small"
                                                items={[
                                                    {
                                                        key: "1",
                                                        label: "Chit Fund Document",
                                                        children: (
                                                            <Fragment>
                                                                {find?.documents && (
                                                                    <>
                                                                        {find?.documents.toLowerCase().endsWith(
                                                                            ".pdf"
                                                                        ) ? (
                                                                            <iframe
                                                                                title="PDF Preview"
                                                                                style={{
                                                                                    width: "100%",
                                                                                    height: "80vh",
                                                                                    border: "none",
                                                                                }}
                                                                                src={find?.documents}
                                                                            />
                                                                        ) : find?.documents.toLowerCase().endsWith(
                                                                            ".docx"
                                                                        ) ||
                                                                            find?.documents.toLowerCase().endsWith(
                                                                                ".doc"
                                                                            ) ? (
                                                                            <iframe
                                                                                title="Document Preview"
                                                                                style={{
                                                                                    width: "100%",
                                                                                    height: "80vh",
                                                                                    border: "none",
                                                                                }}
                                                                                src={`https://docs.google.com/gview?url=${find?.documents}&embedded=true`}
                                                                            />
                                                                        ) : null}
                                                                    </>
                                                                )}
                                                            </Fragment>
                                                        ),
                                                    },
                                                ]}
                                            />
                                        </Col>}
                                </CustomRow>
                            </div>
                        ))}
                    </Col>

                    <Col span={24} md={12}>

                    </Col>
                </CustomRow>

            </CustomCardView>
            <CustomModal
                isVisible={isModalOpen}
                handleOk={handleOk}
                handleCancel={handleCancel}
                width={modelwith}
                modalTitle={modalTitle}
                modalContent={modalContent}
            />
        </Form>
    )
}

export default ChitFundListView