import './productPreloader.scss'


const ProductPreloader = () => {

    window.scrollTo(0,0)
    
    return ( 
        <section className='skeleton-product'>
            <div>
                <div></div>
                <div></div>
            </div>

        <div>
            <div className='skeleton-radio'>
                <ul>
                    <li></li>
                    <li></li>
                    <li></li>
                </ul>
            </div>

            <div className="skeleton-dropdown">
                
            </div>

            <div className='skeleton-product-wrapper'>
                <div className="skeleton-products">
                    {[...Array(12)].map((x, index) => (
                        <div key={index}>
                            <div></div>
                            <div>
                                <ul>
                                    <li></li>
                                    <li></li>
                                    <li></li>
                                    <li></li>
                                </ul>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    </section>
     );
}

export default ProductPreloader;