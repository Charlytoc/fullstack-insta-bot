import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Root from "./routes/root/Root";
import Login from "./routes/login/Login";
import Signup from "./routes/signup/Signup";
import { rootLoader } from "./routes/root/rootLoader";
import AuthorizePage from "./routes/authorize/Authorize";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Root />,
    loader: rootLoader
  },
  {
    path: "/login",
    element: <Login />,

  },
  {
    path: "/signup",
    element: <Signup />,
  },
  {
    path: "/authorize",
    element: <AuthorizePage />,
  },
  
]);

function Routing() {
  return <RouterProvider router={router} />;
}

export default Routing;
