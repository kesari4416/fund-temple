import React, { useEffect, useState } from 'react'
import styled from 'styled-components'
import { useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { setCredentials, selectCurrentUser } from '@modules/Auth/authSlice'
import SignInForm from './SignInForm'
import { baseRequest } from '@request/request'
import { OpenNotification } from '@components/common'
import { toast } from 'react-toastify'
import { APIURLS } from '@request/apiUrls/urls'

export const Wrapper = styled.div`
  height: 100vh;
  width: 100%;
  margin:auto;
  display:grid;
  background:
    radial-gradient(1200px 600px at 80% -10%, rgba(212, 160, 23, 0.10), transparent 60%),
    radial-gradient(900px 500px at -10% 110%, rgba(6, 95, 70, 0.10), transparent 60%),
    #F4F8F5;
`

const SignInCard = styled.div`
  background-color: #fff;
  backdrop-filter:blur(1px);
  padding: 40px 32px;
  max-width: 450px;
  width: 100%;
  margin: auto;
  /* height: 50%; */
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08), 0 0 0 1px rgba(6,95,70,0.06);
`

const UserSignin = () => {

  const navigate = useNavigate()
  const dispatch = useDispatch();
  
  const [isLoading, setIsLoading] = useState(false)

  const handleSignIn = async (data) => {
    setIsLoading(true)
    try {
      const authData = await baseRequest.post(`${APIURLS.LOGIN}`, {
        ...data,
      })
      // console.log(authData,'authData');
      // Mock API, add the origin API and payload data
      if (authData?.data !== '') {

        localStorage.setItem('persist', JSON.stringify(authData?.data))
        dispatch(setCredentials(authData.data))
        OpenNotification({
          type: 'success',
          msg: `Welcome Back ${authData.data?.username}`
        })
        navigate('/',{ replace: true })
        // navigate('/', { replace: true })

      }
      else {
        toast.error('UserName or Password is incorrect ')
      }
    } catch (error) {
      // console.log(error,'error');
      if(error?.response?.status === 401){
        toast.error('Unauthorized access. Please contact the admin !')
        setIsLoading(false)
      }
      else{
        toast.error('Network error: Unable to connect to the server !')
        console.error('Getting error while login', error)
        setIsLoading(false)
      }
      
    }finally{
      setIsLoading(false)
    }
  }
  
  const token = useSelector(selectCurrentUser);

  useEffect(() => {
    if (token) {
      // if()
      navigate('/signin')
    }
  }, [token])

  return (
    <Wrapper column>
      <SignInCard>
        <SignInForm handleSignIn={handleSignIn} isLoading={isLoading}/>
      </SignInCard>
    </Wrapper>
  )
}
export default UserSignin
