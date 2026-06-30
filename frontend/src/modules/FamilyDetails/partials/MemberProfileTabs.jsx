import { Button, CustomDateRangePicker, CustomInputNumber, CustomTable } from '@components/form'
import { CustomStandardTable } from '@components/form/CustomStandardTable'
import { CustomRow, Flex } from '@components/others'
import { APIURLS } from '@request/apiUrls/urls'
import errorHandler from '@request/errorHandler'
import request from '@request/request'
import successHandler from '@request/successHandler'
import { Col, Form } from 'antd'
import dayjs from 'dayjs'
import React, { useEffect, useRef, useState } from 'react'
import { FaWhatsapp } from 'react-icons/fa'
import { IoPrint } from 'react-icons/io5'
import { useReactToPrint } from 'react-to-print'
import CommonManagePrint from './TabPrintPages/CommonManagePrint'
import styled from 'styled-components'
import { toast } from 'react-toastify'

const PrintHolder = styled.div`
    padding: 10px 15px;
    @media print{     
      .PrintShowDatadd {
        display: block;
        page-break-before: always;
        border: 1px solid;
      };
      margin: 50px;
      width:100%;
      margin:auto;
    };
`

const PrintShowData = styled.div`
  display: none;
`

export const MemberPendingAmount = ({ datas }) => {

    const BalanSheetdata = datas?.pending || []

    const totalAmt = datas?.pending_amt_total || 0

    const TabPendingAmount = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Date',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (created_at) => {
                const date = new Date(created_at);
                return date.toLocaleDateString();
            },
        },
        {
            title: 'Particulars',
            dataIndex: 'collection_category'
        },
        {
            title: 'Amount',
            dataIndex: 'amount'
        },

    ]

    return (
        <div>
            <CustomRow>
                <Col span={24} md={24}>
                    <CustomTable columns={TabPendingAmount} data={BalanSheetdata} />
                </Col>
                <Col span={24} md={24}>
                    <Flex flexend={'right'} margin={"20px 0px"} gap={'20px'}>
                        <p style={{ marginTop: "10px" }}>Total</p>
                        <CustomInputNumber value={totalAmt} disabled={true} />
                    </Flex>
                </Col>
            </CustomRow>
        </div>
    )
}

export const MemberBalanceReport = ({ datas }) => {

    const componentRef = useRef();
    const BalanSheetdata = datas?.balance_sheet || []
    const BalanSheetID = datas?.profile

    const TabPaidHistory = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Date',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (created_at) => {
                const date = new Date(created_at);
                return date.toLocaleDateString();
            },
        },
        {
            title: 'Particulars',
            dataIndex: 'name'
        },
        {
            title: 'Name',
            dataIndex: 'name_type'
        },
        {
            title: 'Credit',
            dataIndex: 'amount_balance'
        },
        {
            title: 'Debit',
            dataIndex: 'total_paid_amt'
        },
        {
            title: 'Balance',
            dataIndex: 'total_bal_amt'
        },
        {
            title: 'Penalty',
            dataIndex: 'penalty',
            render: (penalty) => {
                const PenaltyStatus = penalty == true ? <div style={{ color: 'green' }}>Yes</div> : <div style={{ color: 'red' }}>No</div>
                return PenaltyStatus;
            }
        },

    ]

    const handlePrint = useReactToPrint({
        content: () => componentRef.current,
    });

    return (
        <div>
            <Flex end style={{ marginTop: "10px" }}>
                <a href="https://web.whatsapp.com/" target="blank">
                    <Button.Primary text={"Share"} icon={<FaWhatsapp />} />
                </a>
                <Button.Secondary text={"Print"} icon={<IoPrint />}
                    onClick={handlePrint}
                />
            </Flex>
            <CustomStandardTable columns={TabPaidHistory} data={BalanSheetdata} />

            <PrintHolder ref={componentRef}>
                <PrintShowData className="PrintShowDatadd">
                    <CommonManagePrint ProfileRecord={BalanSheetID} /><br />
                    <h3 style={{ marginLeft: '10px' }}>Report Details :-</h3><br />
                    <CustomStandardTable columns={TabPaidHistory} data={BalanSheetdata} pagination={false} />
                </PrintShowData>
            </PrintHolder>
        </div>
    )
}

export const MemberBalanceSheet = ({ datas }) => {

    const [form] = Form.useForm();
    const componentRef = useRef();
    const [tableData, setTableData] = useState([])
    const [filterTableData, setFilterTableData] = useState([])
    const [dateRange, setDateRange] = useState(dayjs().format("YYYY-MM-DD"));

    let BalanSheetdata
    if (filterTableData.length > 1) {
        BalanSheetdata = filterTableData
    } else {
        BalanSheetdata = datas?.temple_mem_balancesheet
    }

    const BalanSheetID = datas?.profile

    const TransformArray = (array) => {
        let previousBalanceAmt = "0.00"; // Initialize the previous balance amount
        for (let i = 0; i < array.length; i++) {
            if (i === 0) {
                array[i].pre_balance_amt = "0.00"; // For the first row, set balance_amt to "0.00"
            } else {
                array[i].pre_balance_amt = previousBalanceAmt; // For subsequent rows, set balance_amt to the previous balance amount
            }
            previousBalanceAmt = array[i].balance_amt; // Update the previous balance amount for the next iteration
        }
        return array;
    }

    useEffect(() => {
        let transformedArray = TransformArray(BalanSheetdata);
        setTableData(transformedArray)
        setFilterTableData(transformedArray)
    }, [BalanSheetdata])




    const handleDateRangeChange = (dates) => {
        setDateRange(dates);
    };

    const BalanceSheetPost = async (data) => {
        await request.post(`${APIURLS.MEMBER_BALANCESHEET_FROMTODATE_POST}`, data)
            .then(function (response) {
                setFilterTableData(response.data?.table)

                if (response.data?.table?.length) {
                    toast.success(
                        "Member Balance Sheet filtered by date successfully retrieved."
                    );
                } else {
                    toast.warn(
                        "There is no data available for this date!"
                    );
                }
                return response.data;

            })
            .catch(function (error) {
                errorHandler(error);
            })
    }


    const onFinish = (data) => {
        const record = { ...data, dateRange, BalanSheetID }
        let NewData = {
            id: record?.BalanSheetID?.id,
            start_date: record?.dateRange?.start_date,
            end_date: record?.dateRange?.end_date,
        }
        BalanceSheetPost(NewData)
    }

    const onSubmit = (data) => {
        form.submit(data);
    }

    const handlePrint = useReactToPrint({
        content: () => componentRef.current,
    });

    const TabPaidHistory = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Date',
            dataIndex: 'reportdate',
        },
        {
            title: 'Particulars',
            dataIndex: 'type_choice'
        },
        {
            title: 'Name',
            dataIndex: 'name_type'
        },
        {
            title: 'Pre Balance',
            dataIndex: 'pre_balance_amt'
        },
        {
            title: 'Credit',
            dataIndex: 'credit_amt'
        },
        {
            title: 'Debit',
            dataIndex: 'debit_amt'
        },
        {
            title: 'Balance',
            dataIndex: 'balance_amt'
        },

    ]
    return (
        <div>
            <Form
                name='memberBalancesheet'
                form={form}
                onFinish={onFinish}
                autoComplete='off'
                labelCol={{ span: 24 }}
                wrapperCol={{ span: 24 }}>

                <Flex style={{ marginTop: "10px" }}>
                    <a href="https://web.whatsapp.com/" target="blank">
                        <Button.Primary text={"Share"} icon={<FaWhatsapp />} />
                    </a>
                    <Button.Secondary text={"Print"} icon={<IoPrint />}
                        onClick={handlePrint}
                    />
                </Flex>

                <Flex end={true} aligncenter={true}>
                    <h4>Search&nbsp;: </h4>&nbsp;&nbsp;
                    <CustomDateRangePicker
                        name={"startend"}
                        onChange={handleDateRangeChange}
                        rules={[{ required: true, message: "Required" }]}
                    />
                    <div style={{ marginTop: '-10px', marginLeft: '5px' }}>
                        <Button.Danger text={"Submit"} onClick={onSubmit} />
                    </div>

                </Flex>
                <CustomStandardTable columns={TabPaidHistory} data={filterTableData} />

                <PrintHolder ref={componentRef}>
                    <PrintShowData className="PrintShowDatadd">
                        <CommonManagePrint ProfileRecord={BalanSheetID} /><br />
                        <h3 style={{ marginLeft: '10px' }}>Balance Sheet Details :-</h3><br />
                        <CustomStandardTable columns={TabPaidHistory} data={tableData} pagination={false} />
                    </PrintShowData>
                </PrintHolder>
            </Form>
        </div >
    )
}

export const MemberHistoryofPenalty = ({ datas }) => {

    const penaltyHistry = datas?.penalty_histry || []

    const totalAmt = datas?.pending_amt_total || 0


    const TabMemberHistoryofPenalty = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Date',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (created_at) => {
                const date = new Date(created_at);
                return date.toLocaleDateString();
            },
        },
        {
            title: 'Penalty Name',
            dataIndex: 'name'
        },
        {
            title: 'Penalty Amount',
            dataIndex: 'penalty_amount'
        },

    ]

    return (
        <div>
            <CustomRow>
                <Col span={24} md={24}>
                    <CustomTable columns={TabMemberHistoryofPenalty} data={penaltyHistry || []} />
                </Col>
                <Col span={24} md={24}>
                    <Flex flexend={'right'} margin={"20px 0px"} gap={'20px'}>
                        <p style={{ marginTop: "10px" }}>Total</p>
                        <CustomInputNumber value={totalAmt} disabled={true} />
                    </Flex>
                </Col>
            </CustomRow>
        </div>
    )
}

export const MemberPaidHistory = ({ datas }) => {

    const componentRef = useRef();
    const BalanSheetID = datas?.profile
    const paidHistry = datas?.paid_histry || []
    const totalAmt = datas?.paid_amt_total || 0

    const TabMemberPaidHistory = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Date',
            dataIndex: 'pay_date'
        },
        {
            title: 'Particulars',
            dataIndex: 'collection_category'
        },
        {
            title: 'Transaction Type',
            dataIndex: 'transaction_type'
        },
        {
            title: 'Amount',
            dataIndex: 'amount'
        },

    ]

    const handlePrint = useReactToPrint({
        content: () => componentRef.current,
    });

    const formatIndianNumber = (number) => {
        const strNumber = number.toString();
        const length = strNumber.length;
        if (length <= 3) {
            return strNumber;
        }
        const lastThreeDigits = strNumber.substring(length - 3);
        const mainPart = strNumber.substring(0, length - 3).replace(/\B(?=(\d{2})+(?!\d))/g, ",");
        return `${mainPart},${lastThreeDigits}`;
    };


    return (
        <div>
            <Flex end style={{ marginTop: "10px" }}>
                <a href="https://web.whatsapp.com/" target="blank">
                    <Button.Primary text={"Share"} icon={<FaWhatsapp />} />
                </a>
                <Button.Secondary text={"Print"} icon={<IoPrint />}
                    onClick={handlePrint}
                />
            </Flex>
            <CustomRow>
                <Col span={24} md={24}>
                    <CustomStandardTable columns={TabMemberPaidHistory} data={paidHistry || []} />
                </Col>
                <Col span={24} md={24}>
                    <Flex flexend={'right'} margin={"20px 0px"} gap={'20px'}>
                        <p style={{ marginTop: "10px" }}>Total</p>
                        <CustomInputNumber value={formatIndianNumber(totalAmt)} disabled={true} />
                    </Flex>
                </Col>
            </CustomRow>
            <PrintHolder ref={componentRef}>
                <PrintShowData className="PrintShowDatadd">
                    <CommonManagePrint ProfileRecord={BalanSheetID} /><br />
                    <h3 style={{ marginLeft: '10px' }}>Paid History Details :-</h3><br />
                    <CustomStandardTable columns={TabMemberPaidHistory} data={paidHistry} pagination={false} />
                    <Flex aligncenter flexend={'right'} margin={"20px"} gap={'20px'}>
                        <h4>Total :</h4><h4>₹ {formatIndianNumber(totalAmt)} </h4>
                    </Flex>
                </PrintShowData>
            </PrintHolder>
        </div>
    )
}

export const MemberChitFundList = () => {

    const TabPaidHistory = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Date',
            dataIndex: 'Date'
        },
        {
            title: 'Credit',
            dataIndex: 'Mode'
        },
        {
            title: 'Debit',
            dataIndex: 'Amount'
        },
        {
            title: 'Balance',
            dataIndex: 'Amount'
        },
    ]

    return (
        <div>
            <CustomTable columns={TabPaidHistory} />
        </div>
    )
}

export const MemberInterestHistory = () => {

    const TabPaidHistory = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Date',
            dataIndex: 'Date'
        },
        {
            title: 'Credit',
            dataIndex: 'Mode'
        },
        {
            title: 'Debit',
            dataIndex: 'Amount'
        },
        {
            title: 'Balance',
            dataIndex: 'Amount'
        },

    ]

    return (
        <div>
            <CustomTable columns={TabPaidHistory} />

        </div>
    )
}
