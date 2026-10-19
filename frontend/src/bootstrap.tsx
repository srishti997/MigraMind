import React from 'react';
import {createRoot} from 'react-dom/client';
import {Authentication} from './Authentication';
createRoot(document.getElementById('root')!).render(<React.StrictMode><Authentication/></React.StrictMode>);
