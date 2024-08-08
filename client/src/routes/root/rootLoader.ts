import { redirect } from "react-router-dom";

export async function rootLoader({
    // @ts-ignore
  request,
}): Promise<any> {
  document.title = "Loading...";
  let url = request.url;
  // const userLanguage = navigator.language;
//   const localStorage = useLocalStorage();
  const search = new URLSearchParams(url.split("?")[1]);
  const nextUrl = search.get("next");
  if (nextUrl) {
    return redirect(nextUrl);
  }
  
  

  return {"message": "Hello"
  };
}
