import React, { useLayoutEffect, useState } from 'react'
import { BodyContent, ContentLayout, HeaderNav, LogoutBottom, MainLayout, MenuBottom, SideMenuLayout, TopHeader } from '@layout/Partials/Style'
import { Drawer, Layout } from 'antd'
import { Button } from '@components/form'
import { SideMenu } from '@layout/Partials/SideMenu'
import { NavHeader } from '@layout/Partials/DynamicSubmenu/NavHeader'
import { CustomModal, Flex } from '@components/others'
import { HiOutlineLogout } from 'react-icons/hi'
import { useDispatch } from 'react-redux'
import { logOut } from '@modules/Auth/authSlice'
import { SvgIcons } from '@assets/Svg'

const DashboardLayout = ({ children }) => {

    const dispatch = useDispatch()
    const [collapsed, setCollapsed] = useState(false);
    const [open, setOpen] = useState(false);
    const [placement, setPlacement] = useState('left');

    // ======  Modal Open ========
    const [isModalOpen, setIsModalOpen] = useState(false);

    // ======  Modal Title and Content ========
    const [modalTitle, setModalTitle] = useState("");
    const [modalContent, setModalContent] = useState(null);

    // ===== Modal Functions Start =====

    const showModal = () => {
        setIsModalOpen(true);
    };

    const handleOk = () => {
        setIsModalOpen(false);
    };

    const handleCancel = () => {
        setIsModalOpen(false);
    };

    const updateCollapse = () => {
        setCollapsed(!collapsed)
    }

    useLayoutEffect(() => {
        window.scrollTo(0, 0)
    }, [location.pathname])

    const showDrawer = () => {
        setOpen(true);
    };

    const onClose = () => {
        setOpen(false);
    };

    const onChange = (e) => {
        setPlacement(e.target.value);
    };

    const AdminLogOut = () => {
        setModalContent(<LogOutModal />);
        setModalTitle("Log Out");
        showModal();
    }

    const LogOutModal = () => (
        <div>
            <h1 style={{ fontSize: '1.2rem' }}>Are you Sure You Want to Logout ?</h1>
            <br />
            <Flex gap={'20px'} W_100 center verticallyCenter>
                <Button.Primary text={'Logout'} onClick={Signout} />
                <Button.Secondary text={'Cancel'} onClick={handleOk} />
            </Flex>
        </div>
    )

    const Signout = () => {
        dispatch(logOut());
        localStorage.removeItem('openKeys')
    }
    return (
        <MainLayout>
            <Layout>
                <SideMenuLayout width={'280'} trigger={null} collapsible collapsed={collapsed}>
                    <HeaderNav style={{ padding: '17px 21px 0px' }}>
                        {/* <span icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                            onClick={() => setCollapsed(!collapsed)}
                        /> */}
                        <span onClick={() => setCollapsed(!collapsed)}>
                            {collapsed ? <img src={SvgIcons.Logoimg} width={'40px'} style={{ marginLeft: '10px' }} /> : <img src={SvgIcons.Logoimg} width={'50px'} style={{ marginLeft: '10px' }} />}
                        </span>

                        <h3 className={collapsed ? 'active' : ''} style={{ fontFamily: 'rubik', fontSize: 32, fontWeight: 600, paddingLeft: 0 }}>Temple</h3>
                    </HeaderNav>
                    <SideMenu collapsed={collapsed} />
                    <MenuBottom onClick={AdminLogOut}>
                        <Flex aligncenter={true} >
                            <HiOutlineLogout style={{ fontSize: '22px', color: '#fff' }} />
                            {collapsed ? '' : <h1 style={{ color: '#fff' }}>Log Out</h1>}
                        </Flex>
                    </MenuBottom>
                </SideMenuLayout>

                <Drawer
                    title="TEMPLE"
                    placement={placement}
                    closable={false}
                    onClose={onClose}
                    open={open}
                    key={placement}
                    width={250}>
                    <SideMenu collapsed={collapsed} />
                    <LogoutBottom onClick={AdminLogOut}>
                        <Flex aligncenter={true} style={{ gap: '10px' }} >
                            <HiOutlineLogout size={20} />
                            <h1 style={{ fontSize: 'large' }}>Log Out</h1>
                        </Flex>
                    </LogoutBottom>
                </Drawer>
                <ContentLayout $collapsed={collapsed}>
                    <TopHeader
                    >

                        <NavHeader updateCollapse={updateCollapse} showDrawer={showDrawer} />
                    </TopHeader>
                    <BodyContent
                        style={{
                            margin: '1px 1px',
                            padding: 24,
                        }}>
                        {children}
                    </BodyContent>
                </ContentLayout>
            </Layout>
            <CustomModal isVisible={isModalOpen} handleOk={handleOk} handleCancel={handleCancel}
                width={600} modalTitle={modalTitle} modalContent={modalContent} />
        </MainLayout>
    )
}

export default DashboardLayout
