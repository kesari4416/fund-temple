import { CustomRow } from '@components/others'
import { CustomPageTitle } from '@components/others/CustomPageTitle';
import { Col } from 'antd'
import React from 'react'
import { TotalStyle } from '../../ChitProfitDistribution/Partials/ProfitDistributionView';


const ViewChitFundSettlementAppln = ({ settleRecord }) => {
    return (
        <TotalStyle>
            <CustomPageTitle Heading={'View Settlement Application'} />
            <CustomRow space={[12, 12]}>
                <Col span={24} md={12}>
                    <h1>chit fund name : <span>{settleRecord?.chit_fund_name}</span></h1>
                </Col>
                <Col span={24} md={12}>
                    <h1>Investor Name : <span>{settleRecord?.invester_name}</span></h1>
                </Col>
                <Col span={24} md={12}>
                    <h1>Settlement Aplication No : <span>{settleRecord?.settlement_aplication_no}</span></h1>
                </Col>
                <Col span={24} md={12}>
                    <h1>Settlement Date : <span>{settleRecord?.settlement_date}</span></h1>
                </Col>
                <Col span={24} md={12}>
                    <h1>Invested Amount : <span>₹ {Number(settleRecord?.investment_amt || 0).toFixed(2)}</span></h1>
                </Col>
                <Col span={24} md={12}>
                    <h1>Share Count : <span>{settleRecord?.share_count ?? 0}</span></h1>
                </Col>
                <Col span={24} md={12}>
                    <h1>Share Amount : <span>₹ {Number(settleRecord?.share_amount || 0).toFixed(2)}</span></h1>
                </Col>
                <Col span={24} md={12}>
                    <h1>Total Amount : <span style={{ color: '#0F5132', fontWeight: 700 }}>₹ {Number(settleRecord?.total_amount || 0).toFixed(2)}</span></h1>
                </Col>
            </CustomRow>
        </TotalStyle>
    )
}

export default ViewChitFundSettlementAppln