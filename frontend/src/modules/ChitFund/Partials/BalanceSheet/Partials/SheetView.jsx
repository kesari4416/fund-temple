import { CustomStandardTable } from "@components/form/CustomStandardTable"
import { Fragment } from "react"

export const ChitfundInvesView = ({ datas }) => {
    const ColumnTable = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Income Name',
            dataIndex: 'name'
        },
        {
            title: 'Amount',
            dataIndex: 'amount'
        },
    ]
    return (
        <Fragment>
            {datas?.map((item, index) => (
                <div key={index}>
                    <h4 style={{color:'#990000'}}>{item?.chitfund_name}</h4>
                    <CustomStandardTable columns={ColumnTable} data={item?.details} pagination={false} />
                </div>
            ))}
        </Fragment>
    )
}

export const ChitfundInterestGivenView = ({ datas }) => {

    const ValuesData = datas?.Chit_fund_Interest_Given?.details || []

    const ColumnTable = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Name',
            dataIndex: 'name'
        },
        {
            title: 'Amount',
            dataIndex: 'amount'
        },
    ]

    return (
        <div>
            <CustomStandardTable columns={ColumnTable} data={ValuesData} pagination={false} />
        </div>
    )
}

export const CFProfitDistributionView = ({ datas }) => {

    const ValuesData = datas?.Chit_fund_Profit_Distribution?.details || []

    const ColumnTable = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Name',
            dataIndex: 'name'
        },
        {
            title: 'Amount',
            dataIndex: 'amount'
        },
    ]

    return (
        <div>
            <CustomStandardTable columns={ColumnTable} data={ValuesData} pagination={false} />
        </div>
    )
}

export const FromCollectionView = ({ datas }) => {

    const ValuesData = datas?.From_Collection?.details || []

    const ColumnTable = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Name',
            dataIndex: 'name'
        },
        {
            title: 'Amount',
            dataIndex: 'amount'
        },
    ]

    return (
        <div>
            <CustomStandardTable columns={ColumnTable} data={ValuesData} pagination={false} />
        </div>
    )
}