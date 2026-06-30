import React, { Fragment, useEffect } from 'react'
import { Routes, Route, useNavigate } from 'react-router-dom'
import { anonymous } from '@router/config/routes'
import AuthPage from '@router/components/AuthPage'

const AuthRouter = ({ isAuthenticated }) => {

  const navigate = useNavigate()

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/signin')
    }
  }, [isAuthenticated])

  return (
    <Fragment>
      {
        isAuthenticated ? (
          <AuthPage isAuthenticated={isAuthenticated} />
        ) :
          (
            <Routes>
              {anonymous.map(({ routePath, Component }) => {
                return (
                  <Route
                    key={routePath}
                    path={routePath}
                    element={<Component />}
                  ></Route>
                )
              })}
            </Routes>
          )
      }
    </Fragment>
  )
}

export default AuthRouter
